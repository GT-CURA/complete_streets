import osmnx as ox
import networkx as nx
import geopandas as gpd
from shapely.geometry import Point
from typing import Set
from shapely.geometry import box

def download_drivenetwork(place):
    poly = place.union_all()

    desired_types = {
        "trunk","primary","secondary","tertiary",
        "residential","living_street","pedestrian"
    }

    G_Drive = ox.graph_from_polygon(
        poly,
        network_type="drive",
        retain_all=False,
        truncate_by_edge=True
    )

    # optional post-filter for highway classes
    edges_to_remove = [
        (u, v, k) for u, v, k, data in G_Drive.edges(keys=True, data=True)
        if "highway" not in data or not any(hwy_type in data["highway"] for hwy_type in desired_types)
    ]

    G_Drive.remove_edges_from(edges_to_remove)
    G_Drive.remove_nodes_from(list(nx.isolates(G_Drive)))

    gdf_edges = ox.graph_to_gdfs(G_Drive, nodes=False)
    gdf_edges = gdf_edges.reset_index()
    gdf_edges = gdf_edges[['u', 'v', 'key', 'osmid', 'highway', 'name', 'length', 'geometry']]

    return gdf_edges

def download_walknetwork(buffer):
    minx, miny, maxx, maxy = buffer.total_bounds
    bbox = (minx, miny, maxx, maxy)
    G_Walk = ox.graph.graph_from_bbox(bbox, network_type='walk')
    return G_Walk

def compute_isochrones1(points_gdf, G, radius=700):
    records = []
    for idx, geom in enumerate(points_gdf.geometry):
        try:
            center = ox.distance.nearest_nodes(G, X=geom.x, Y=geom.y)
            subg = nx.ego_graph(G, center, radius=radius, distance="length")
            pts = [Point(data["x"], data["y"]) for _, data in subg.nodes(data=True)]
            hull = gpd.GeoSeries(pts, crs=points_gdf.crs).union_all().convex_hull
            records.append(hull)

        except Exception as e:
            print(f"Error at point {idx}: {e}")
            continue

    points_isochrones = points_gdf.copy()
    points_isochrones['geometry'] = records

    return points_isochrones

def compute_isochrones(stops,G):
    RAIL_TYPES = {1, 2, 5, 12}
    records_700 = []
    records_100_rail = []
    for sid, geom, rtype in zip(stops['stop_id'], stops.geometry, stops['route_type']):
        try:
            center = ox.distance.nearest_nodes(G, X=geom.x, Y=geom.y)

            # 700m buffer for all modes
            subg_700 = nx.ego_graph(G, center, radius=700, distance='length')
            pts_700 = [Point(data['x'], data['y']) for _, data in subg_700.nodes(data=True)]
            if pts_700:
                hull_700 = gpd.GeoSeries(pts_700).union_all().convex_hull
                records_700.append({'stop_id': sid, 'route_type': rtype, 'geometry': hull_700})

            # 100m buffer for rail modes only
            if rtype in RAIL_TYPES:
                subg_100 = nx.ego_graph(G, center, radius=100, distance='length')
                pts_100 = [Point(data['x'], data['y']) for _, data in subg_100.nodes(data=True)]
                if pts_100:
                    hull_100 = gpd.GeoSeries(pts_100).union_all().convex_hull
                    records_100_rail.append({'stop_id': sid, 'route_type': rtype, 'geometry': hull_100})

        except Exception:
            continue

    def _to_gdf(records):
        if not records:
            return gpd.GeoDataFrame(columns=['stop_id', 'route_type', 'geometry'], crs=stops.crs)
        gdf = gpd.GeoDataFrame(records, crs=stops.crs)
        gdf['stop_id'] = gdf['stop_id'].astype(str)
        gdf = gdf[gdf.geometry.geom_type == "Polygon"].copy()
        return gdf

    isos_700_all  = _to_gdf(records_700)
    isos_100_rail = _to_gdf(records_100_rail)

    isos_700_rail = isos_700_all[isos_700_all['route_type'].isin(RAIL_TYPES)].copy()
    isos_700_bus  = isos_700_all[isos_700_all['route_type'] == 3].copy()

    return (
        isos_700_rail,
        isos_700_bus,
        isos_100_rail,
    )