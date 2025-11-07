#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
import numpy as np
import pandas as pd
import cv2
from shapely.geometry import LineString

#### FILTER HORIZONTAL LINES ####
# Function to calculate the angle of a line
def calculate_line_angle(x1, y1, x2, y2):
    angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
    if angle < 0:
        angle += 360
    return angle

# Function to filter lines by horizontal angles
def filter_horizontal_lines(lines_df, tolerance=10):
    """
    Filter lines that are approximately horizontal based on a given tolerance.
    
    Parameters:
    - lines_df: DataFrame with columns ['x1', 'y1', 'x2', 'y2'].
    - tolerance: The degree tolerance for detecting horizontal lines.
    
    Returns:
    - horizontal_lines_df: DataFrame with filtered horizontal lines.
    """
    horizontal_lines = []
    for _, line in lines_df.iterrows():
        x1, y1, x2, y2 = line['x1'], line['y1'], line['x2'], line['y2']
        angle = calculate_line_angle(x1, y1, x2, y2)
        
        # Check if the angle is within the horizontal tolerance range (around 0° or 180°)
        if (0 <= angle <= tolerance) or (180 - tolerance <= angle <= 180 + tolerance) or (360 - tolerance <= angle <= 360):
            line['angle'] = angle  # Add the calculated angle to the line data
            horizontal_lines.append(line)
    
    return pd.DataFrame(horizontal_lines)


#### ERASE THE OVERLAPPED LINES ####
def create_line_buffer(x1, y1, x2, y2, buffer_distance=5):
    """
    Create a buffer around a line segment.
    
    Parameters:
    - x1, y1: Start point of the line.
    - x2, y2: End point of the line.
    - buffer_distance: The width of the buffer to create around the line.
    
    Returns:
    - buffer_polygon: A polygon representing the buffered line.
    """
    line = LineString([(x1, y1), (x2, y2)])
    buffer_polygon = line.buffer(buffer_distance)
    return buffer_polygon

def remove_overlapping_lines_with_buffer(lines_df, buffer_distance=5, overlap_threshold=0.7):
    """
    Remove lines that overlap significantly based on a buffer intersection.
    
    Parameters:
    - lines_df: DataFrame containing lines with columns ['x1', 'y1', 'x2', 'y2'].
    - buffer_distance: The buffer width around each line.
    - overlap_threshold: The proportion of overlapping area to consider lines as duplicates.
    
    Returns:
    - filtered_lines_df: DataFrame with overlapping lines removed.
    """
    keep_mask = [True] * len(lines_df)
    
    # List to store buffered geometries for each line
    buffers = []
    
    # Create buffers for each line
    for i, row in lines_df.iterrows():
        buffer_polygon = create_line_buffer(row['x1'], row['y1'], row['x2'], row['y2'], buffer_distance)
        buffers.append(buffer_polygon)
    
    # Compare each line's buffer with others to find overlaps
    for i in range(len(lines_df)):
        if not keep_mask[i]:  # Skip if this line has already been marked as a duplicate
            continue
        
        for j in range(i + 1, len(lines_df)):
            if not keep_mask[j]:  # Skip if this line has already been marked as a duplicate
                continue
            
            # Check for buffer intersection
            intersection_area = buffers[i].intersection(buffers[j]).area
            min_area = min(buffers[i].area, buffers[j].area)
            
            # If the overlap is greater than the threshold, mark one line as a duplicate
            if intersection_area / min_area > overlap_threshold:
                keep_mask[j] = False  # Mark the second line as a near-duplicate
    
    # Filter the lines based on the keep mask
    filtered_lines_df = lines_df[keep_mask].reset_index(drop=True)
    
    return filtered_lines_df

