#!/usr/bin/env python
# coding: utf-8

# In[14]:


import geopandas as gpd

def load_midpoints(geojson_path):
    gdf = gpd.read_file(geojson_path)
    gdf_midpoint = gdf[gdf["is_midpoint"] == True]

    link_counts = gdf_midpoint.groupby("link_id").size().reset_index(name="n_points")
    n_links = link_counts["link_id"].nunique()
    both_sides = (link_counts["n_points"] == 2).sum()
    one_side = (link_counts["n_points"] == 1).sum()

    print(n_links, "unique links detected")
    print(both_sides, "link(s) have both sides")
    print(one_side, "link(s) have only one side")

    # return dictionary of {link_id: df}
    return {lid: grp for lid, grp in gdf_midpoint.groupby("link_id")}

