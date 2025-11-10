import folium
import branca.colormap as cm
import webbrowser
import os
import geopandas as gpd

def plot(score_gdf, place, score_column="Transit_attribute", filename="Transit_Attributes_Map.html"):
    score_gdf = score_gdf.copy()

    # Compute center of the place geometry for map centering
    geom = place.geometry.unary_union
    center_point = geom.centroid
    center = [center_point.y, center_point.x]
    m = folium.Map(location=center, zoom_start=12, tiles="CartoDB dark_matter")

    # Define colormap
    colormap = cm.linear.RdYlBu_05.scale(score_gdf[score_column].min(), score_gdf[score_column].max())

    # Add streets to the map
    for _, row in score_gdf.iterrows():
        if row['geometry'].geom_type == 'LineString':
            coords = [(lat, lon) for lon, lat in row['geometry'].coords]
            folium.PolyLine(
                locations=coords,
                color=colormap(row[score_column]),
                weight=1.5,
                opacity=0.7,
                tooltip=folium.Tooltip(
                    f"Score: {row[score_column]:.2f}<br>Street Name: {row['name']}"
                    )
            ).add_to(m)

    colormap.caption = score_column
    colormap.add_to(m)

    legend_css = """
    <style>
    .legend {
        color: white !important;
    }
    </style>
    """
    m.get_root().header.add_child(folium.Element(legend_css))

    # Save
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    m.save(filename)