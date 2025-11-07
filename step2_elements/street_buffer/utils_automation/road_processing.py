#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
import numpy as np
import pandas as pd
import cv2
import matplotlib.pyplot as plt
from skimage.measure import label, regionprops

from image_processing_a import filter_horizontal_lines, remove_overlapping_lines_with_buffer
from image_processing_b import add_unique_id_to_lines, segment_all_lines_by_vertical_boundaries, vertical_boundaries


def process_road_edges(pixel_df, img_path, save_dir, pitch):
    """
    Detect road edges from segmentation results.
    Focuses on extracting the TOP edge of the road.
    """

    # 1. Make grayscale mask for road
    road_grayscale_image = np.zeros(
        (pixel_df['y'].max() + 1, pixel_df['x'].max() + 1), dtype=np.uint8
    )
    road_pixels = pixel_df[pixel_df['label'] == 'road']
    road_grayscale_image[road_pixels['y'], road_pixels['x']] = 255

    # 2. Remove small road blobs
    labeled_image, _ = label(road_grayscale_image, return_num=True, connectivity=2)
    props = regionprops(labeled_image)
    small_road_threshold = (640 * 640) / (14**2)

    mask = np.zeros_like(road_grayscale_image)
    for prop in props:
        if prop.area < small_road_threshold:
            mask[labeled_image == prop.label] = 255
    road_clean = road_grayscale_image.copy()
    road_clean[mask == 255] = 0

    if not np.any(road_clean):
        print(f"⚠️ No road detected for {img_path}")
        return None, 0

    # 3. Edge detection
    edges = cv2.Canny(road_clean, 30, 100, apertureSize=5)
    if edges is None or not np.any(edges):
        print(f"⚠️ No edges detected for {img_path}")
        return None, 1

    # 4. Line detection
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=25,
                            minLineLength=20, maxLineGap=30)
    if lines is None:
        print(f"⚠️ No lines detected for {img_path}")
        return None, 2

    lines_df = pd.DataFrame([line[0] for line in lines], columns=["x1", "y1", "x2", "y2"])

    # 5. Horizontal filtering + overlap removal
    horiz_df = filter_horizontal_lines(lines_df, tolerance=10)
    filtered_df = remove_overlapping_lines_with_buffer(horiz_df, buffer_distance=5, overlap_threshold=0.7)

    # 6. Segment lines by vertical boundaries
    lines_with_id = add_unique_id_to_lines(filtered_df)
    segmented_df = segment_all_lines_by_vertical_boundaries(lines_with_id, vertical_boundaries)

    if segmented_df.empty:
        print(f"⚠️ No valid segmented lines for {img_path}")
        return None, 3

    # Add the pitch value as "case" column
    segmented_df["case"] = pitch

    # 7. Visualization (final only)
    plt.figure(figsize=(10, 10))
    plt.imshow(np.zeros_like(road_clean), cmap='gray')
    for _, r in segmented_df.iterrows():
        plt.plot([r['x1'], r['x2']], [r['y1'], r['y2']], color='cyan', linewidth=2)
    plt.gca()
    out_path = os.path.join(save_dir, os.path.basename(img_path).replace(".jpg", "_road_lines.jpg"))
    plt.savefig(out_path, bbox_inches='tight', pad_inches=0)
    plt.close()

    print(f"✅ Road edge lines saved → {out_path}")
    return segmented_df, None


def filter_top_road_edge(road_lines_df):
    """
    Filter to keep only the TOP edge of the road.
    For each cluster, keep the line with the smallest y-value (topmost).
    """
    if road_lines_df.empty:
        return road_lines_df
    
    # Group by cluster and case, then keep the line with minimum y-value
    top_edges = []
    for (cluster, case), group in road_lines_df.groupby(['cluster', 'case']):
        # Find the line with the smallest average y-value (topmost)
        group['y_avg'] = (group['y1'] + group['y2']) / 2
        top_line = group.loc[group['y_avg'].idxmin()]
        top_edges.append(top_line)
    
    top_edges_df = pd.DataFrame(top_edges).reset_index(drop=True)
    
    # Label all as 'top' type for consistency
    top_edges_df['type'] = 'top'
    
    return top_edges_df

