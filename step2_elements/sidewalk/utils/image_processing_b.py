import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cv2
from skimage.measure import regionprops
from shapely.geometry import LineString, Polygon, Point, MultiPoint, GeometryCollection
from image_processing_a import create_line_buffer

def add_unique_id_to_lines(lines_df):
    """
    Add a unique ID to each line in the DataFrame based on its index.
    
    Parameters:
    - lines_df: DataFrame containing the lines.
    
    Returns:
    - lines_df: DataFrame with an added 'line_id' column.
    """
    # Add a new column 'line_id' based on the row index
    lines_df['line_id'] = [str(i + 1) for i in range(len(lines_df))]
    return lines_df

# Function to segment a line based on vertical boundaries
def segment_line_by_vertical_boundaries(x1, y1, x2, y2, vertical_boundaries):
    """
    Segment a line based on the provided vertical boundaries.
    
    Parameters:
    - x1, y1: Coordinates of the starting point of the line.
    - x2, y2: Coordinates of the ending point of the line.
    - vertical_boundaries: A list of x-values representing vertical boundaries.
    
    Returns:
    - segments: A list of dictionaries, each representing a segment with new start and end points.
    """
    segments = []
    # Sort the vertical boundaries for safety
    vertical_boundaries = sorted(vertical_boundaries)
    
    # Iterate through each boundary to create segments
    start_x, start_y = x1, y1
    for boundary in vertical_boundaries:
        # Check if the boundary intersects the line
        if x1 < boundary < x2 or x2 < boundary < x1:
            # Calculate the intersection point (boundary, y at that x)
            slope = (y2 - y1) / (x2 - x1) if x2 != x1 else float('inf')  # Avoid division by zero for vertical lines
            new_y = y1 + slope * (boundary - x1)
            
            # Create the new segment from the start to the boundary
            segment = {
                'x1': start_x,
                'y1': start_y,
                'x2': boundary,
                'y2': new_y
            }
            segments.append(segment)
            
            # Update the start point for the next segment
            start_x, start_y = boundary, new_y
    
    # Add the final segment from the last boundary to the end of the line
    final_segment = {
        'x1': start_x,
        'y1': start_y,
        'x2': x2,
        'y2': y2
    }
    segments.append(final_segment)
    
    return segments


# Function to apply the segmentation logic to all lines in the DataFrame
def segment_all_lines_by_vertical_boundaries(lines_df, vertical_boundaries):
    """
    Apply the segmentation logic to all lines in the DataFrame based on vertical boundaries.
    
    Parameters:
    - lines_df: DataFrame containing the lines with columns ['x1', 'y1', 'x2', 'y2', 'line_id'].
    - vertical_boundaries: A list of x-values representing vertical boundaries.
    
    Returns:
    - segmented_lines_df: DataFrame with segmented lines, keeping track of the original line_id.
    """    
    all_segments = []
    
    # Loop through each line in the DataFrame
    for _, row in lines_df.iterrows():
        line_id = row['line_id']
        x1, y1, x2, y2 = row['x1'], row['y1'], row['x2'], row['y2']
        
        # Segment the line using the segmentation function
        segments = segment_line_by_vertical_boundaries(x1, y1, x2, y2, vertical_boundaries)
        
        # Add the line_id and cluster to each segment and append to the list
        for i, segment in enumerate(segments):
            segment['line_id'] = f'{line_id}_{i+1}'  # Label each segment with the original line_id and segment number
            
            # Determine the cluster based on the segment's x-coordinates
            if segment['x1'] < segment['x2']:
                x_start, x_end = segment['x1'], segment['x2']
            else:
                x_start, x_end = segment['x2'], segment['x1']
            
            # Find which cluster the segment belongs to
            for j in range(len(vertical_boundaries) - 1):
                if vertical_boundaries[j] <= x_start < vertical_boundaries[j + 1]:
                    segment['cluster'] = j + 1
                    break
            
            all_segments.append(segment)
    
    # Convert the list of segments into a DataFrame
    segmented_lines_df = pd.DataFrame(all_segments)
    return segmented_lines_df


vertical_boundaries = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 
                   110, 120, 130, 140, 150, 160, 170, 180, 190, 200,
                   210, 220, 230, 240, 250, 260, 270, 280, 290, 300, 
                   310, 320, 330, 340, 350, 360, 370, 380, 390, 400, 
                   410, 420, 430, 440, 450, 460, 470, 480, 490, 500, 
                   510, 520, 530, 540, 550, 560, 570, 580, 590, 600,
                   610, 620, 630, 640
                  ]     

def cluster_score(geom_groups):
    return sum(group_freq.get(g, 0) for g in geom_groups)