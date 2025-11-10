import geopandas as gpd
import pandas as pd
import numpy as np

def scoring(points, iso, streets):
    #print("Debug: Check CRS: ", "iso:", iso.crs, "point:",points.crs, streets.crs)
    joined_gdf = gpd.sjoin(points, iso, how="left", predicate="intersects")

    # Convert index to column for grouping
    joined_gdf = joined_gdf.reset_index()

    # Summarize significance per point
    collapsed_gdf = joined_gdf.groupby("index", as_index=False).agg({
    "name": "first",
    "link_id": "first",
    "geometry": "first",
    "significance": "sum"
    })
    collapsed_gdf = collapsed_gdf.rename(columns={"significance": "sig_sum_per_point"})

    # Add count of stops contributing to each point
    collapsed_gdf["stops_count"] = joined_gdf.groupby("index")["significance"].count().values

    # Compute mean significance per point
    if collapsed_gdf["stops_count"].eq(0).all():
        print("⚠️ There are no stops contributing to any points. All 'stops_count' are zero.")

    collapsed_gdf['sig_mean_per_point'] = (
        collapsed_gdf['sig_sum_per_point'] / collapsed_gdf['stops_count']
    ).where(collapsed_gdf['stops_count'] != 0, 0)

    # Group by link_id to compute street-level scores
    scoredStreet = collapsed_gdf.groupby(["link_id"], as_index=False).agg(
        points_count=("sig_sum_per_point", "count"),
        stops_computecount=("stops_count", "sum"),
        sig_mean_mean=("sig_mean_per_point", "mean"),
    )

    # Fill NaN values with 0
    scoredStreet['sig_mean_mean'] = scoredStreet['sig_mean_mean'].fillna(0)

    # Final Score Calculation
    scoredStreet['Score'] = scoredStreet['sig_mean_mean']*(np.log((scoredStreet['stops_computecount']/scoredStreet['points_count'])+1))
    
    # Convert to GeoDataFrame and merge geometry
    streets = streets.drop(columns=['midpoint', 'points'], errors='ignore')
    scoredStreet = scoredStreet.merge(
        streets[['name', 'link_id', 'geometry']],
        on=['link_id'],
        how='left'
    )
    scoredStreet = gpd.GeoDataFrame(
        scoredStreet,
        geometry='geometry',
        crs=streets.crs
    )
    return scoredStreet