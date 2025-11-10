import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from zipfile import ZipFile, is_zipfile, BadZipFile
from pandas.errors import EmptyDataError

def load_gtfs_from_zip(zip_path: str, filename: str) -> pd.DataFrame | None:
    if not is_zipfile(zip_path):
        return None
    try:
        with ZipFile(zip_path) as z:
            if z.testzip():
                return None
            if filename not in z.namelist():
                return None
            with z.open(filename) as f:
                try:
                    return pd.read_csv(f, low_memory=False)
                except EmptyDataError:
                    return None
    except BadZipFile:
        return None

def process_single_gtfs_zip(zip_path: str, tag: str):
    stops      = load_gtfs_from_zip(zip_path, "stops.txt")
    routes     = load_gtfs_from_zip(zip_path, "routes.txt")
    trips      = load_gtfs_from_zip(zip_path, "trips.txt")
    stop_times = load_gtfs_from_zip(zip_path, "stop_times.txt")
    calendar   = load_gtfs_from_zip(zip_path, "calendar.txt")

    if any(df is None for df in (stops, routes, trips, stop_times, calendar)):
        print(f"⚠️[SKIP] Required File does not exist in GTFS: {zip_path}")
        return None

    required_columns_map = [
        (trips, ["trip_id", "route_id", "service_id"]),
        (routes, ["route_id"]),
        (stop_times, ["trip_id", "stop_id"]),
        (stops, ["stop_id"])
    ]

    for df, cols in required_columns_map:
        missing = [col for col in cols if col not in df.columns]
        if missing:
            print(f"⚠️ [SKIP] Missing columns {missing} in GTFS: {zip_path}")
            return None
        for col in cols:
            df[col] = df[col].astype(str)

    # Processing Calendar (Skip if service_id does not exist)
    if calendar is not None:
        if "service_id" not in calendar.columns:
            print(f"⚠️ [SKIP] 'service_id' column missing in calendar.txt: {zip_path}")
            return None
        calendar["service_id"] = calendar["service_id"].astype(str)
        calendar["service_id"] = tag + "_" + calendar["service_id"]

    # Tagging IDs
    for df, mapping in [
        (trips,    {"trip_id":tag+"_","route_id":tag+"_","service_id":tag+"_"}),
        (routes,   {"route_id":tag+"_"}),
        (stop_times,{"trip_id":tag+"_", "stop_id":tag+"_"}),
        (stops, {"stop_id": tag+"_"})
    ]:
        for col, prefix in mapping.items():
            df[col] = prefix + df[col]
        
    # Merging DataFrames
    merged = (
        stop_times[["trip_id", "arrival_time", "departure_time", "stop_id"]]
        .merge(trips[["trip_id","route_id","service_id"]], on="trip_id", how="left")
        .merge(routes[["route_id","route_type"]], on="route_id", how="left")
    )

    if calendar is not None:
        merged = merged.merge(calendar, on="service_id", how="left")

    merged["source"] = tag
    stops["source"] = tag
    trips["source"] = tag
    routes["source"] = tag
    if calendar is not None:
        calendar["source"] = tag

    return merged, stops, trips, routes, calendar

def stops_bymodes(sched_merged, stops_merged):
    TYPE_MAPPING = {
        0: 'Streetcar',
        1: 'Subway',
        2: 'Rail_long',
        3: 'Bus',
        4: 'Ferry',
        5: 'Tram',
        6: 'Cable car',
        7: 'Funicular',
        11: 'Trolleybus',
        12: 'Monorail'
    }

    sched_merged['station_type'] = sched_merged['route_type'].map(TYPE_MAPPING).fillna('Others')

    station_modes = (
        sched_merged[['stop_id', 'station_type', 'route_type', 'route_id']]
        .drop_duplicates()
        .groupby(['stop_id', 'station_type', 'route_type'])
        .agg(routes=('route_id', lambda seq: list(set(seq))))
        .reset_index()
    )

    # Create a unique identifier for each stop-mode combination
    station_modes['stop_id_mode'] = station_modes['stop_id'].astype(str) + "_" + station_modes['station_type']

    # Merge with stops to get Geo information
    stops_sel = stops_merged.drop(
        ['stop_code', 'stop_desc', 'zone_id', 'stop_url', 'location_type', 'parent_station', 'stop_timezone', 'wheelchair_boarding'],
        axis=1, errors='ignore'
    )

    # Merge to get full stop information
    station_modes_full = station_modes.merge(stops_sel, on='stop_id', how='left')

    # Create GeoDataFrame
    station_modes_gdf = gpd.GeoDataFrame(
        station_modes_full,
        geometry=[Point(xy) for xy in zip(station_modes_full['stop_lon'], station_modes_full['stop_lat'])],
        crs="EPSG:4326"
    )

    return station_modes_gdf

def concat_dataframes(dl_dir: str):
    merged_list = []
    stops_list = []

    for fname in os.listdir(dl_dir):
        if not fname.endswith(".zip"):
            continue

        tag = fname.replace(".zip", "")
        result = process_single_gtfs_zip(os.path.join(dl_dir, fname), tag)

        if result is None:
            continue

        merged, stops, *_ = result

        if merged is None or merged.empty or merged.isna().all().all():
            print(f"⚠️ Skipped {tag}: empty or NA-only DataFrame")
            continue

        merged_list.append(merged)
        stops_list.append(stops)

    sched_merged = pd.concat(merged_list, ignore_index=True)
    stops_merged = pd.concat(stops_list, ignore_index=True)
    stops_bymode = stops_bymodes(sched_merged, stops_merged)
    
    return sched_merged, stops_bymode, tag