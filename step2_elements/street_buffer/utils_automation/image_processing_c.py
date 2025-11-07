#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cv2
from skimage.measure import regionprops
from shapely.geometry import LineString, Polygon, Point, MultiPoint, GeometryCollection
from image_processing_a import create_line_buffer

def assign_top_or_bottom_and_filter(lines_df):
    """
    Add a 'type' column to the DataFrame, indicating whether each line is 'top' or 'bottom' in its cluster and case.
    Also, remove lines that do not get a 'top' or 'bottom' label.
    
    Parameters:
    - lines_df: DataFrame containing lines with columns ['x1', 'y1', 'x2', 'y2', 'cluster', 'case'].
    
    Returns:
    - filtered_lines_df: DataFrame with the added 'type' column and empty rows filtered out.
    """
    # Initialize an empty 'type' column
    lines_df['type'] = ''

    # Group by both 'cluster' and 'case' to make sure each group is handled separately
    for (cluster, case), group in lines_df.groupby(['cluster', 'case']):
        # Sort the lines in the group by their y-values (y1 and y2) to identify top/bottom
        group_sorted = group.copy()
        group_sorted['y_min'] = group_sorted[['y1', 'y2']].min(axis=1)  # Find the smallest y-value
        group_sorted['y_max'] = group_sorted[['y1', 'y2']].max(axis=1)  # Find the largest y-value
        
        # Sort the group by the y_min (ascending order)
        group_sorted = group_sorted.sort_values(by='y_min', ascending=True)
        
        # The first line (lower y-value) will be the "top" and the second line (higher y-value) will be the "bottom"
        if len(group_sorted) >= 2:  # Ensure there are at least two lines in the group
            lines_df.loc[group_sorted.index[0], 'type'] = 'top'
            lines_df.loc[group_sorted.index[1], 'type'] = 'bottom'

    # Filter out rows where 'type' is still empty (i.e., lines that were not assigned 'top' or 'bottom')
    filtered_lines_df = lines_df[lines_df['type'] != ''].reset_index(drop=True)

    return filtered_lines_df


# Function to calculate the midpoint of a line
def calculate_midpoint(x1, y1, x2, y2):
    return (x1 + x2) / 2, (y1 + y2) / 2

# Function to calculate the Euclidean distance between two points
def calculate_distance(x1, y1, x2, y2):
    return np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

# Function to add 'dist_btwn' and 'dist_central' columns
def add_distances(lines_df):
    """
    Add 'dist_btwn' and 'dist_central' columns to the DataFrame.
    
    Parameters:
    - lines_df: DataFrame containing lines with columns ['x1', 'y1', 'x2', 'y2', 'cluster', 'case', 'type'].
    
    Returns:
    - lines_df: DataFrame with added 'dist_btwn' and 'dist_central' columns.
    """
    # Initialize empty columns
    lines_df['dist_btwn'] = np.nan
    lines_df['dist_central_abs'] = np.nan
    lines_df['dist_central'] = np.nan
    
    
    central_line_y = 320  # The y-value of the central horizontal line

    # Group by 'cluster' and 'case' to calculate distances for each group
    for (cluster, case), group in lines_df.groupby(['cluster', 'case']):
        # Separate top and bottom lines
        top_line = group[group['type'] == 'top']
        bottom_line = group[group['type'] == 'bottom']

        if len(top_line) == 1 and len(bottom_line) == 1:  # Ensure there's one top and one bottom line
            # Calculate midpoints for the top and bottom lines
            top_mid_x, top_mid_y = calculate_midpoint(top_line['x1'].values[0], top_line['y1'].values[0], 
                                                      top_line['x2'].values[0], top_line['y2'].values[0])
            bottom_mid_x, bottom_mid_y = calculate_midpoint(bottom_line['x1'].values[0], bottom_line['y1'].values[0], 
                                                            bottom_line['x2'].values[0], bottom_line['y2'].values[0])
            
            # Calculate distance between top and bottom midpoints (dist_btwn)
            dist_btwn = calculate_distance(top_mid_x, top_mid_y, bottom_mid_x, bottom_mid_y)
            
            # Assign dist_btwn to both top and bottom lines in the group
            lines_df.loc[top_line.index, 'dist_btwn'] = dist_btwn
            lines_df.loc[bottom_line.index, 'dist_btwn'] = dist_btwn

        # Calculate dist_central for each line in the group
        for idx, row in group.iterrows():
            mid_x, mid_y = calculate_midpoint(row['x1'], row['y1'], row['x2'], row['y2'])
            dist_central_abs = abs(mid_y - central_line_y)  # Distance to the central line
            dist_central = (mid_y - central_line_y)  # Distance to the central line
            lines_df.loc[idx, 'dist_central_abs'] = dist_central_abs
            lines_df.loc[idx, 'dist_central'] = dist_central

    return lines_df


def create_final_result_df(combined_lines_df_with_distances):
    """
    Create a final result DataFrame that includes the average dist_central values for 'top' and 'bottom' types,
    grouped by 'case' (0 or -10).
    
    Parameters:
    - filtered_nearby_clusters_df: DataFrame with the filtered nearby clusters.
    
    Returns:
    - final_result_df: DataFrame with average dist_central values for 'top' and 'bottom' types, grouped by case.
    """
    # Group by 'case' and 'type', then calculate the average dist_central
    grouped = combined_lines_df_with_distances.groupby(['case', 'type'])['dist_central'].mean().unstack()
    
    return grouped

