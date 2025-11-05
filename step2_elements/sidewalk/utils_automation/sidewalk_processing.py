import os
import numpy as np
import pandas as pd
import cv2
import matplotlib.pyplot as plt
from skimage.measure import label, regionprops

from image_processing_a import filter_horizontal_lines, remove_overlapping_lines_with_buffer
from image_processing_b import add_unique_id_to_lines, segment_all_lines_by_vertical_boundaries, vertical_boundaries

def process_sidewalk_edges(pixel_df, img_path, save_dir, pitch):
    """
    Detect sidewalk edges from segmentation results.
    Keeps only final visualization (no intermediate plots).
    """

    # 1. Make grayscale mask for sidewalk
    sidewalk_grayscale_image = np.zeros(
        (pixel_df['y'].max() + 1, pixel_df['x'].max() + 1), dtype=np.uint8
    )
    sidewalk_pixels = pixel_df[pixel_df['label'] == 'sidewalk']
    sidewalk_grayscale_image[sidewalk_pixels['y'], sidewalk_pixels['x']] = 255

    # 2. Remove small sidewalk blobs
    labeled_image, _ = label(sidewalk_grayscale_image, return_num=True, connectivity=2)
    props = regionprops(labeled_image)
    small_sidewalk_threshold = (640 * 640) / (14**2)

    mask = np.zeros_like(sidewalk_grayscale_image)
    for prop in props:
        if prop.area < small_sidewalk_threshold:
            mask[labeled_image == prop.label] = 255
    sidewalk_clean = sidewalk_grayscale_image.copy()
    sidewalk_clean[mask == 255] = 0

    if not np.any(sidewalk_clean):
        print(f"⚠️ No sidewalk detected for {img_path}")
        return None, 0

    # 3. Edge detection
    edges = cv2.Canny(sidewalk_clean, 30, 100, apertureSize=5)
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

    # 🔑 Add the pitch value as "case" column
    segmented_df["case"] = pitch

    # 7. Visualization (final only)
    plt.figure(figsize=(10, 10))
    plt.imshow(np.zeros_like(sidewalk_clean), cmap='gray')
    for _, r in segmented_df.iterrows():
        plt.plot([r['x1'], r['x2']], [r['y1'], r['y2']], color='lime', linewidth=2)
    plt.gca()
    out_path = os.path.join(save_dir, os.path.basename(img_path).replace(".jpg", "_final_lines.jpg"))
    plt.savefig(out_path, bbox_inches='tight', pad_inches=0)
    plt.close()

    print(f"✅ Final sidewalk edge pairs saved → {out_path}")
    return segmented_df, None


####
from image_processing_c import (
    assign_top_or_bottom_and_filter,
    add_distances,
    create_final_result_df
)
from calculation import equations_top, equations_bottom
from scipy.optimize import fsolve
import numpy as np
import matplotlib.pyplot as plt
import os


def estimate_sidewalk_width(combined_lines_df, save_dir, link_id=None, side=None):
    """
    Take combined horizontal lines from side1 & side2,
    assign top/bottom, compute distances, and estimate sidewalk width.
    """
    # Step 1: assign top/bottom and compute distances
    combined_lines_df_with_type = assign_top_or_bottom_and_filter(combined_lines_df)
    combined_lines_df_with_distances = add_distances(combined_lines_df_with_type)
    final_result_df = create_final_result_df(combined_lines_df_with_distances)

    # Step 2: visualization
    plt.figure(figsize=(6.4, 6.4))
    cases = combined_lines_df_with_distances['case'].unique()
    color_map = plt.get_cmap('tab10')
    for _, row in combined_lines_df_with_distances.iterrows():
        color = color_map(cases.tolist().index(row['case']))
        plt.plot([row['x1'], row['x2']], [row['y1'], row['y2']], color=color, linewidth=2)
    plt.axhline(y=320, color='red', linestyle='--', label='Central Line (y = 320)', linewidth=1.5)
    plt.xlim([0, 640])
    plt.ylim([0, 640])
    plt.gca().invert_yaxis()
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('Lines with Central Line and dist_btwn Labels (No Decimal Points)')
    plt.grid(True)
    plt.legend()
    plot_path = os.path.join(save_dir, "top_bottom_edges.jpg")
    plt.savefig(plot_path, bbox_inches='tight', pad_inches=0)
    plt.close()

    print(f"\n✅ Paired Top and Bottom Edges for {link_id} | {side}:")
    print(final_result_df)

    # Step 3: extract points at pitch=0 and pitch=-10
    try:
        p_0_top = final_result_df.loc[0, 'top']
        p_10_top = final_result_df.loc[-10, 'top']
        p_0_bottom = final_result_df.loc[0, 'bottom']
        p_10_bottom = final_result_df.loc[-10, 'bottom']
    except KeyError:
        print("⚠️ Missing top/bottom data for pitch=0 or pitch=-10")
        return None

    # Step 4: solve for target pitch using your equations
    T_init_top = 8 if p_10_top < 0 else 13
    T_init_bottom = 8 if p_10_bottom < 0 else 13
    T_sol_top = fsolve(equations_top, T_init_top, args=(p_0_top, p_10_top))
    T_sol_bottom = fsolve(equations_bottom, T_init_bottom, args=(p_0_bottom, p_10_bottom))

    print(f"Potential Target Pitch (TOP) [{link_id} | {side}]: ", T_sol_top)
    print(f"Potential Target Pitch (BOTTOM) [{link_id} | {side}]: ", T_sol_bottom)

    # Step 5: compute width
    T_top = T_sol_top[0]
    T_bottom = T_sol_bottom[0]
    cot_T_top = 1 / np.tan(np.radians(T_top))
    cot_T_bottom = 1 / np.tan(np.radians(T_bottom))

    width = 2.5 * (cot_T_top - cot_T_bottom)
    print(f"✅ Estimated Sidewalk Width ({link_id} | {side}): {width}")

    return width