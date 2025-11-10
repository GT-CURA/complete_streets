import pandas as pd
import geopandas as gpd
import json
from shapely.geometry import Point
import os


def stop_significance(
    stops_within_iso: gpd.GeoDataFrame,
    stops_bymode: gpd.GeoDataFrame,
    isos_100_rail: gpd.GeoDataFrame,
    iso_700_bus: gpd.GeoDataFrame,
    iso_700_rail: gpd.GeoDataFrame,
    sched_merged: pd.DataFrame,
    target_crs: str,
    tag: str
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:

    # 0) Divide stops by mode
    busstops_gdf  = stops_within_iso[stops_within_iso['route_type'] == 3].copy()
    railstops_gdf = stops_within_iso[stops_within_iso['route_type'].isin([0, 1, 2, 5, 12])].copy()

    busstops_all  = stops_bymode[stops_bymode['route_type'] == 3].copy()
    railstops_all = stops_bymode[stops_bymode['route_type'].isin([0, 1, 2, 5, 12])].copy()

    # 1) Factor E
    factor_e_bus  = compute_factor_e(busstops_gdf)
    factor_e_rail = compute_factor_e(railstops_gdf)

    # 2) Factor S
    factor_s_bus = bus_compute_factor_s(
        busstops=busstops_gdf,
        busstops_all=busstops_all,
        railstops=railstops_gdf,
        isos_100_rail=isos_100_rail,
        target_crs=target_crs
    )

    factor_s_rail = rail_compute_factor_s(
        stops_gdf=stops_bymode,
        rail_100_iso=isos_100_rail
    )

    # 3) Factor F
    rail_types = [0, 1, 2, 5, 12]

    sched_bus = (
        sched_merged[sched_merged["route_type"] == 3]
        .loc[lambda df: df["stop_id"].isin(busstops_gdf["stop_id"])]
        .copy()
    )
    sched_rail = (
        sched_merged[sched_merged["route_type"].isin(rail_types)]
        .loc[lambda df: df["stop_id"].isin(railstops_gdf["stop_id"])]
        .copy()
    )

    factor_f_bus  = compute_factor_f(sched_bus,  all_stop_ids=busstops_gdf['stop_id'])
    factor_f_rail = compute_factor_f(sched_rail, all_stop_ids=railstops_gdf['stop_id'])

    # 4) Factor Q
    bus_factor_q = compute_factor_q(
        busstops_gdf=busstops_gdf,
        tag=tag,
        target_crs=target_crs
    )
    json_path = 'data/amenities/all_scores.json'
    rail_factor_q_scalar = 2.5 if os.path.exists(json_path) else 0.5

    # 5) Bus Stop Significance
    bus_analysis = (
        busstops_gdf[['stop_id', 'route_type']]
        .merge(factor_e_bus[['stop_id','routes','factor_e']], on='stop_id', how='left')
        .merge(factor_s_bus, on='stop_id', how='left')
        .merge(factor_f_bus, on='stop_id', how='left')
        .merge(bus_factor_q, on='stop_id', how='left')
    )

    bus_analysis[['factor_e','factor_s','factor_f','factor_q']] = (
        bus_analysis[['factor_e','factor_s','factor_f','factor_q']].fillna(0)
    )

    bus_analysis['significance'] = (
        bus_analysis['factor_e'] * bus_analysis['factor_s'] * bus_analysis['factor_f']
        + bus_analysis['factor_q']
    )

    for c in ['routes', 'stop_rate_h']:
        if c in bus_analysis.columns:
            bus_analysis = bus_analysis.drop(columns=[c])

    bus_iso_scored = iso_700_bus.merge(bus_analysis, on='stop_id', how='left')

    # 6) Railway Significance
    rail_analysis = (
        railstops_gdf[['stop_id', 'route_type']]
        .merge(factor_e_rail[['stop_id','routes','factor_e']], on='stop_id', how='left')
        .merge(factor_s_rail, on='stop_id', how='left')
        .merge(factor_f_rail, on='stop_id', how='left')
    )

    rail_analysis[['factor_e','factor_s','factor_f']] = (
        rail_analysis[['factor_e','factor_s','factor_f']].fillna(0)
    )

    rail_analysis['significance'] = (
        rail_analysis['factor_e'] * rail_analysis['factor_s'] * rail_analysis['factor_f']
        + rail_factor_q_scalar
    )

    for c in ['routes', 'stop_rate_h']:
        if c in rail_analysis.columns:
            rail_analysis = rail_analysis.drop(columns=[c])

    rail_iso_scored = iso_700_rail.merge(rail_analysis, on='stop_id', how='left')

    return bus_iso_scored, rail_iso_scored

##--------------------------------------------------------------------------
## Factor_E: Number of Routes
##--------------------------------------------------------------------------

def compute_factor_e(stops: gpd.GeoDataFrame) -> pd.DataFrame:
    factor_e_df = stops[['stop_id', 'routes']].copy()
    factor_e_df['factor_e'] = factor_e_df['routes'].apply(score_e)
    return factor_e_df

def score_e(routes):
    E = len(routes) if isinstance(routes, (list, set, tuple)) else 0
    return 0.5 + 0.5 * min(E, 3)


##--------------------------------------------------------------------------
# Bus_Factor_S: Number of Routes connected to Rail Station
##--------------------------------------------------------------------------

def bus_score_s(route_set, near_rail_df):
    # Among the route sets of rail stops located within a 100 m walking distance, check how many routes overlap with the route sets of each bus stop located within a 3 km radius.
    nearby_routes = set().union(*near_rail_df['routes_set'])
    matched = route_set & nearby_routes
    return 1 + 0.5 * min(len(matched), 2)

def bus_compute_factor_s(busstops, busstops_all, railstops, isos_100_rail, target_crs):
    # 0) Match CRS
    B = busstops.to_crs(target_crs).copy()
    B_all = busstops_all.to_crs(target_crs).copy()
    R = railstops.to_crs(target_crs).copy()
    ISO = isos_100_rail.to_crs(target_crs).copy()

    # 1) Compute 3km buffer around each bus stop
    Bbuf = B[['stop_id', 'geometry']].copy()
    Bbuf['geometry'] = Bbuf.geometry.buffer(3000)

    # 2) Match rail stops within 3km of bus stops
    rail_in_3km = gpd.sjoin(
        R[['stop_id', 'geometry']], Bbuf,
        how='inner', predicate='within',
        lsuffix='rail', rsuffix='bus'
    ).drop(columns=['index_right'], errors='ignore')

    # Dictionary: bus stop ID -> list of rail stop IDs within 3km
    bus_to_rails = (
        rail_in_3km.groupby('stop_id_bus')['stop_id_rail']
        .apply(list).to_dict()
        if len(rail_in_3km) > 0 else {}
    )

    # Match rail stops within 100m isochrone
    near_bus = gpd.sjoin(
        B_all[['stop_id','routes','geometry']], ISO[['stop_id','geometry']],
        how='inner', predicate='within', lsuffix='bus', rsuffix='rail'
    ).drop(columns=['index_right'], errors='ignore')

    def norm_set(x):
        if isinstance(x, (list, set, tuple)): return set(x)
        if pd.isna(x): return set()
        return {x}

    rail_routes_map = (
        near_bus.groupby('stop_id_rail')['routes']
        .apply(lambda s: set().union(*[norm_set(v) for v in s]))
        .to_dict()
        if len(near_bus) > 0 else {}
    )

    # Compute factor_s for each bus stop
    def score_row(row):
        my_routes = norm_set(row['routes'])
        rails = bus_to_rails.get(row['stop_id'], [])
        if not rails:
            return 1.0
        union_routes = set().union(*[rail_routes_map.get(r, set()) for r in rails])
        matched = my_routes & union_routes
        return 1.0 + 0.5 * min(len(matched), 2)

    out = B[['stop_id','routes']].copy()
    out['factor_s'] = out.apply(score_row, axis=1)
    return out[['stop_id','factor_s']]

##--------------------------------------------------------------------------
## Railway_Factor_S: Number of Bus Stops nearby Rail Station
##--------------------------------------------------------------------------
def rail_compute_factor_s(stops_gdf: gpd.GeoDataFrame,
                          rail_100_iso: gpd.GeoDataFrame) -> pd.DataFrame:
    
    busstops_gdf = stops_gdf[stops_gdf['route_type']==3]
    # Spatial join: find all bus stops within each station's 100 m isochrone
    try:
        joined = gpd.sjoin(
            busstops_gdf[['stop_id', 'geometry']],
            rail_100_iso[['stop_id', 'geometry']],
            how='inner',
            predicate='within',
            lsuffix='bus',
            rsuffix='rail'
        )
    except Exception as e:
        raise RuntimeError(f"Spatial join failed: {e}")

    # Count bus stops per rail station
    counts = (
        joined
        .groupby('stop_id_rail')
        .size()
        .rename('S_r')
        .reset_index()
    )

    # Compute factor_s with a cap at 2 stops
    counts['factor_s'] = 1 + 0.5 * counts['S_r'].clip(upper=2)

    # Merge back to include stations with zero bus stops (factor_s = 1)
    counts = counts.rename(columns={'stop_id_rail': 'stop_id'})
    result = (
        rail_100_iso[['stop_id']]
        .merge(counts[['stop_id', 'factor_s']], on='stop_id', how='left')
        .fillna({'factor_s': 1})
    )

    return result[['stop_id', 'factor_s']]

##--------------------------------------------------------------------------
## Factor_F: Frequency
##--------------------------------------------------------------------------

def score_f(w: float) -> float:
    if w < 2.0:    return 1.00
    if w < 3.0:    return 1.25
    if w < 4.0:    return 1.50
    if w <= 6.0:   return 1.75
    return 2.00

def compute_factor_f(sched: pd.DataFrame, all_stop_ids=None) -> pd.DataFrame:
    weekdays = ['monday','tuesday','wednesday','thursday','friday']
    daily_rates = []
    sched = sched.copy()
    sched['arr_td'] = pd.to_timedelta(sched['arrival_time'])
    sched['dep_td'] = pd.to_timedelta(sched['departure_time'])

    # Peak hours: 7–9am, 4–7pm
    morning_start, morning_end = 6 * 3600, 9 * 3600
    evening_start, evening_end = 16 * 3600, 19 * 3600
    fixed_duration_h = 6.0

    for day in weekdays:
        col = sched.get(day)
        if col is None or col.dropna().nunique() <= 1:
            df_day = sched.copy()
        else:
            df_day = sched[col == 1].copy()

        df_day = df_day.drop_duplicates(subset=['stop_id','route_id','arr_td','dep_td'])
        df_day = df_day.dropna(subset=['arr_td'])

        secs = df_day['arr_td'].dt.total_seconds().astype(int)
        is_peak = (
            secs.between(morning_start, morning_end, inclusive='left') |
            secs.between(evening_start, evening_end, inclusive='left')
        )
        df_peak = df_day[is_peak]

        group_cols = ['stop_id', 'route_id', 'service_id']
        if 'direction_id' in df_peak.columns:
            group_cols.insert(2, 'direction_id')

        span = (df_peak.groupby(group_cols)
                      .size()
                      .reset_index(name='count_peak'))

        span['duration_h'] = fixed_duration_h
        span['rate_h'] = span['count_peak'] / span['duration_h']

        rate = (span.groupby(['stop_id','route_id'])['rate_h']
                    .mean().reset_index(name=f'rate_{day}'))
        daily_rates.append(rate)

    from functools import reduce
    rates_merged = (reduce(lambda L, R: L.merge(R, on=['stop_id','route_id'], how='outer'),
                           daily_rates)
                    if daily_rates else pd.DataFrame(columns=['stop_id','route_id']))

    rate_cols = [f'rate_{d}' for d in weekdays if f'rate_{d}' in rates_merged.columns]
    if not rate_cols:
        factor_f_df = rates_merged[['stop_id']].drop_duplicates()
        factor_f_df['stop_rate_h'] = 0.0
    else:
        rates_merged['avg_weekday_rate'] = rates_merged[rate_cols].mean(axis=1).fillna(0)
        factor_f_df = (rates_merged.groupby('stop_id')['avg_weekday_rate']
                                  .mean().reset_index(name='stop_rate_h'))

    if all_stop_ids is None:
        all_stop_ids = pd.Index(sched['stop_id'].unique())

    universe = pd.DataFrame({'stop_id': all_stop_ids})
    factor_f_df = universe.merge(factor_f_df, on='stop_id', how='left')

    factor_f_df['stop_rate_h'] = factor_f_df['stop_rate_h'].fillna(0.0)
    factor_f_df['factor_f'] = factor_f_df['stop_rate_h'].apply(score_f)
    return factor_f_df

##--------------------------------------------------------------------------
## 4. Bus Stops Facilities Score
##--------------------------------------------------------------------------

def compute_factor_q(
    busstops_gdf: gpd.GeoDataFrame,
    tag: str,
    target_crs: str) -> pd.DataFrame:
    try:
        with open('data/amenities/all_scores.json') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return pd.DataFrame({
            'stop_id': pd.Index(busstops_gdf['stop_id'].astype(str)).unique(),
            'factor_q': 0.0
        })
        
    qualityScore = (
        pd.DataFrame.from_dict(data, orient='index')
        .assign(stop_id=lambda df: df.index.astype(str).map(lambda x: f"{tag}_{x}"))
        .pipe(lambda df: pd.concat([df.drop(columns='amenity_scores'),
                                    df['amenity_scores'].apply(pd.Series)], axis=1))
        .reset_index(drop=True)
    )

    busstops_gdf_merged = busstops_gdf.merge(
        qualityScore,
        on="stop_id",
        how="left"
    )

    fill_up = pd.read_csv('data/amenities/Inventory.csv')
    fill_up = gpd.GeoDataFrame(
        fill_up,
        geometry=[Point(xy) for xy in zip(fill_up['Lon'], fill_up['Lat'])],
        crs="EPSG:4326"
    ).to_crs(target_crs)

    fill_up = (
        fill_up.rename(columns={"Stop ID": "stop_id"})
                .drop(columns=['Lon', 'Lat', 'geometry', 'Jurisdiction', 'Stop Abbr', 'Stop Name', 'Route(S)'])
                .assign(stop_id=lambda df: df["stop_id"].astype(str)
                                        .map(lambda x: f"{tag}_{x}"))
    )

    busstops_gdf_merged = busstops_gdf_merged.merge(
        fill_up,
        on="stop_id",
        how="left"
    )

    cols = ['shelter','seating','trash can','sign']
    zero_dict = dict.fromkeys(cols, 0)
    mapping = {
        # signs
        'Sign Strapped to Pole': dict(zero_dict, sign=1),
        'Sign on Post':          dict(zero_dict, sign=1),

        # shelters & seats
        'Shelter':               dict(zero_dict, shelter=1, seating=1),
        'Bench':                 dict(zero_dict, seating=1),
        'Simme Seat':            dict(zero_dict, seating=1),

        # movable signs
        'Sign on Moveable on Street': dict(zero_dict, sign=1),
        'Sign on Moveable Pedestal':  dict(zero_dict, sign=1),

        # all 0
        'Stop at Rail Station':  zero_dict,
        'Park and Ride':         zero_dict,
        'Text Painted on Street':zero_dict,
        'Temporary Bus Stop':    zero_dict,
    }

    mask_empty = busstops_gdf_merged[cols].fillna(0).eq(0).all(axis=1)

    for btype, rules in mapping.items():
        sel = mask_empty & (busstops_gdf_merged['Bus Stop Type'] == btype)
        if sel.any():
            for c, v in rules.items():
                busstops_gdf_merged.loc[sel, c] = v

    busstops_gdf_merged[cols] = (
    busstops_gdf_merged[cols]
      .apply(pd.to_numeric, errors='coerce')
      .fillna(0)
      .gt(0)
      .astype('int8')
    )

    def score_q(data):
        shelter_index = 2.0 if data['shelter'] == 1 else 1.0

        amenities_count = (
            data['trash can'] +
            data['seating'] +
            data['sign']
        )

        if amenities_count <= 1:
            amenities_index = 1.0
        elif amenities_count == 2:
            amenities_index = 1.5
        else:
            amenities_index = 2.0

        return (shelter_index * amenities_index) / 2.0

    busstops_gdf_merged['factor_q'] = busstops_gdf_merged.apply(score_q, axis=1)
    factor_q = busstops_gdf_merged[['stop_id', 'factor_q']]
    return factor_q