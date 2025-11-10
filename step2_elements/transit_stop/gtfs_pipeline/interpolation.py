from shapely.geometry import Point
import numpy as np
import geopandas as gpd

def interpolate_roads(streets, target_crs):
    interval = 10

    streets['points'] = streets['geometry'].apply(lambda geom: interpolate_points(geom, interval))

    # Explode points into separate rows
    points_gdf = streets.explode('points', ignore_index=True)
    points_gdf = points_gdf.drop(columns=['geometry']).rename(columns={'points': 'geometry'})
    points_gdf = gpd.GeoDataFrame(points_gdf, geometry='geometry', crs=target_crs)
    points_gdf = points_gdf.to_crs("EPSG:4326")

    return points_gdf

def interpolate_points(line, interval):    
    points = [line.interpolate(distance) for distance in np.arange(0, line.length, interval)]
    if line.coords[-1] not in points:
        points.append(Point(line.coords[-1]))
    return points