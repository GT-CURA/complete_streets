import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import fsolve

from image_processing_c import add_distances
from calculation import equations_top, equations_bottom


def select_bottommost_sidewalk_edges(sidewalk_lines_df, save_dir, link_id=None, side=None):
    """
    Select the bottommost sidewalk edge for each (cluster, case) pair.

    Strategy:
      1. Filter to sidewalk edges where type == 'bottom'.
      2. For each edge, compute y_avg = (y1 + y2) / 2.
      3. For each (cluster, case) group, keep the line with the LARGEST y_avg
         (i.e., visually closest to the bottom of the image).

    Parameters:
    - sidewalk_lines_df: DataFrame with sidewalk edges. Must contain:
        ['x1', 'y1', 'x2', 'y2', 'cluster', 'case', 'type']
    - save_dir: Directory to save visualization
    - link_id: Optional link identifier for plot title
    - side: Optional side identifier for plot title

    Returns:
    - bottommost_sidewalk_df: DataFrame with one bottommost edge per (cluster, case)
    """
    # 1) Filter only bottom sidewalk edges
    sidewalk_bottom = sidewalk_lines_df[sidewalk_lines_df['type'] == 'bottom'].copy()
    if sidewalk_bottom.empty:
        return pd.DataFrame()

    # 2) Compute average y-value (larger y = closer to bottom of image)
    sidewalk_bottom['y_avg'] = (sidewalk_bottom['y1'] + sidewalk_bottom['y2']) / 2

    # 3) For each (cluster, case), keep the line with the largest y_avg
    #    (i.e., the visually bottommost edge for that pitch in that horizontal cluster)
    bottommost_sidewalk_df = (
        sidewalk_bottom
        .sort_values('y_avg')  # sort so tail(1) = largest y_avg
        .groupby(['cluster', 'case'], as_index=False)
        .tail(1)
        .reset_index(drop=True)
    )

    # ===================== VISUALIZATION =====================
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))

    # LEFT PLOT: All sidewalk bottom edges (separated by case)
    ax1.set_xlim([0, 640])
    ax1.set_ylim([0, 640])
    ax1.invert_yaxis()
    ax1.set_title(f'All Sidewalk Bottom Edges\n{link_id} | {side}', fontsize=14, weight='bold')
    ax1.set_xlabel('X (pixels)', fontsize=12)
    ax1.set_ylabel('Y (pixels)', fontsize=12)
    ax1.grid(True, alpha=0.3)

    for _, row in sidewalk_bottom.iterrows():
        if row['case'] == 0:
            color = 'lightcoral'
            linestyle = '--'
        else:  # case == -10
            color = 'lightblue'
            linestyle = '-'
        ax1.plot(
            [row['x1'], row['x2']], [row['y1'], row['y2']],
            color=color, linestyle=linestyle, linewidth=2, alpha=0.6
        )

    from matplotlib.lines import Line2D
    legend_elements_left = [
        Line2D([0], [0], color='lightcoral', linewidth=2, linestyle='--', label='All Pitch 0°'),
        Line2D([0], [0], color='lightblue', linewidth=2, linestyle='-', label='All Pitch -10°'),
    ]
    ax1.legend(handles=legend_elements_left, loc='upper right', fontsize=11)

    # RIGHT PLOT: Only bottommost edges per (cluster, case)
    ax2.set_xlim([0, 640])
    ax2.set_ylim([0, 640])
    ax2.invert_yaxis()
    ax2.set_title(f'Bottommost Sidewalk Edges (Selected)\n{link_id} | {side}', fontsize=14, weight='bold')
    ax2.set_xlabel('X (pixels)', fontsize=12)
    ax2.set_ylabel('Y (pixels)', fontsize=12)
    ax2.grid(True, alpha=0.3)

    for _, row in bottommost_sidewalk_df.iterrows():
        if row['case'] == 0:
            color = 'red'
            linestyle = '--'
        else:  # case == -10
            color = 'blue'
            linestyle = '-'
        ax2.plot(
            [row['x1'], row['x2']], [row['y1'], row['y2']],
            color=color, linestyle=linestyle, linewidth=3
        )

    legend_elements_right = [
        Line2D([0], [0], color='red', linewidth=3, linestyle='--', label='Selected Pitch 0°'),
        Line2D([0], [0], color='blue', linewidth=3, linestyle='-', label='Selected Pitch -10°'),
    ]
    ax2.legend(handles=legend_elements_right, loc='upper right', fontsize=11)

    plt.tight_layout()
    plot_path = os.path.join(save_dir, "sidewalk_bottommost_selection.jpg")
    plt.savefig(plot_path, bbox_inches='tight', pad_inches=0, dpi=150)
    plt.close()

    return bottommost_sidewalk_df


def combine_sidewalk_and_road_edges(sidewalk_lines_df, road_lines_df, save_dir, link_id=None, side=None):
    """
    Combine sidewalk bottom edges with road top edges for buffer width calculation.

    Workflow:
      1. Use select_bottommost_sidewalk_edges() to get one bottommost sidewalk edge
         per (cluster, case).
      2. Find clusters where BOTH pitches (0 and -10) exist for sidewalk bottom edges
         AND both pitches exist for road edges in the same cluster.
      3. Filter to only those "valid" clusters.
      4. Return a combined DataFrame containing:
           - sidewalk bottom edges (type='bottom') for both pitches
           - road top edges   (type='bottom_road') for both pitches

    Parameters:
    - sidewalk_lines_df: DataFrame with sidewalk edges (must have 'type' column with 'bottom' values)
    - road_lines_df: DataFrame with road edges (already filtered to top edges; has 'cluster' and 'case')
    - save_dir: Directory to save visualizations
    - link_id: Link identifier for labeling
    - side: Side identifier for labeling

    Returns:
    - combined_df: DataFrame ready for buffer width calculation with only valid clusters
    """
    # STEP 1: Select bottommost sidewalk edges and visualize
    bottommost_sidewalk_df = select_bottommost_sidewalk_edges(
        sidewalk_lines_df, save_dir, link_id, side
    )

    if bottommost_sidewalk_df.empty:
        return pd.DataFrame()

    # STEP 2: Determine which clusters have sidewalk bottom edges at BOTH pitches (0 and -10)
    required_cases = {0, -10}
    valid_clusters = []

    for cluster in bottommost_sidewalk_df['cluster'].unique():
        sw_cluster = bottommost_sidewalk_df[bottommost_sidewalk_df['cluster'] == cluster]
        sw_cases = set(sw_cluster['case'].unique())

        # Skip if sidewalk doesn't have both pitches
        if not required_cases.issubset(sw_cases):
            continue

        # Check road edges in the same cluster
        rd_cluster = road_lines_df[road_lines_df['cluster'] == cluster]
        rd_cases = set(rd_cluster['case'].unique())

        # Require road edges at both pitches as well
        if required_cases.issubset(rd_cases):
            valid_clusters.append(cluster)

    # STEP 3: Filter sidewalk and road edges to only valid clusters
    if not valid_clusters:
        # No cluster where both sidewalk & road exist at 0 and -10
        return pd.DataFrame()

    bottommost_sidewalk_valid = bottommost_sidewalk_df[
        bottommost_sidewalk_df['cluster'].isin(valid_clusters)
    ].copy()

    road_matched = road_lines_df[road_lines_df['cluster'].isin(valid_clusters)].copy()
    if road_matched.empty:
        return pd.DataFrame()

    # Label road edges as 'bottom_road' so calculate_buffer_width can separate them
    road_matched['type'] = 'bottom_road'

    # STEP 4: Combine both sidewalk and road for valid clusters only
    combined_df = pd.concat([bottommost_sidewalk_valid, road_matched], ignore_index=True)


    return combined_df


# def calculate_buffer_width(combined_df, save_dir, link_id=None, side=None, proximity_threshold=10):
#     """
#     Calculate street buffer width between sidewalk bottom and road top edges.
    
#     Parameters:
#     - combined_df: DataFrame with sidewalk bottom and road top edges
#     - save_dir: Directory to save visualization
#     - link_id: Link identifier for labeling
#     - side: Side identifier for labeling
#     - proximity_threshold: Pixel distance threshold to consider edges as "touching" (no buffer)
    
#     Returns:
#     - buffer_width: Calculated buffer width in meters, or None if edges are touching
#     """
    
#     # Separate sidewalk bottom and road top
#     sidewalk_bottom = combined_df[combined_df['type'] == 'bottom'].copy()
#     road_top = combined_df[combined_df['type'] == 'bottom_road'].copy()
    
#     if sidewalk_bottom.empty or road_top.empty:
#         print(f"⚠️ Missing sidewalk bottom or road top edges for {link_id} | {side}")
#         return None
    
#     # Rename road type to 'top' for distance calculation logic
#     road_top['type'] = 'top'
    
#     # Combine and calculate distances
#     edges_df = pd.concat([sidewalk_bottom, road_top], ignore_index=True)
#     edges_with_distances = add_distances(edges_df)
    
#     # Create summary dataframe
#     summary = edges_with_distances.groupby(['case', 'type'])['dist_central'].mean().unstack()
    
#     # Check if we have data for both pitches
#     try:
#         p_0_sidewalk = summary.loc[0, 'bottom']
#         p_10_sidewalk = summary.loc[-10, 'bottom']
#         p_0_road = summary.loc[0, 'top']
#         p_10_road = summary.loc[-10, 'top']
#     except KeyError:
#         print("⚠️ Missing edge data for pitch=0 or pitch=-10")
#         return None
    
#     # Calculate average distance between edges
#     avg_distance_p0 = abs(p_0_sidewalk - p_0_road)
#     avg_distance_p10 = abs(p_10_sidewalk - p_10_road)
#     avg_distance = (avg_distance_p0 + avg_distance_p10) / 2
    
#     # ========== VISUALIZATION: BUFFER EDGES ==========
#     plt.figure(figsize=(12, 10))
    
#     matched_clusters = sorted(edges_with_distances['cluster'].unique())
    
#     # Draw the selected edges for each pitch
#     for cluster in matched_clusters:
#         cluster_data = edges_with_distances[edges_with_distances['cluster'] == cluster]
        
#         for case in sorted(cluster_data['case'].unique()):
#             pitch_data = cluster_data[cluster_data['case'] == case]
            
#             sidewalk_edge = pitch_data[pitch_data['type'] == 'bottom']
#             road_edge = pitch_data[pitch_data['type'] == 'top']
            
#             linestyle = '--' if case == 0 else '-'
#             alpha = 0.7  # transparency for all lines
            
#             # Sidewalk: blue (0°), sky blue (-10°)
#             if not sidewalk_edge.empty:
#                 sw_row = sidewalk_edge.iloc[0]
#                 if case == 0:
#                     sw_color = 'blue'
#                 else:  # -10
#                     sw_color = 'skyblue'
#                 plt.plot(
#                     [sw_row['x1'], sw_row['x2']],
#                     [sw_row['y1'], sw_row['y2']],
#                     color=sw_color,
#                     linestyle=linestyle,
#                     linewidth=3,
#                     alpha=alpha,
#                 )
            
#             # Road: red (0°), orange (-10°)
#             if not road_edge.empty:
#                 rd_row = road_edge.iloc[0]
#                 if case == 0:
#                     rd_color = 'red'
#                 else:  # -10
#                     rd_color = 'orange'
#                 plt.plot(
#                     [rd_row['x1'], rd_row['x2']],
#                     [rd_row['y1'], rd_row['y2']],
#                     color=rd_color,
#                     linestyle=linestyle,
#                     linewidth=3,
#                     alpha=alpha,
#                 )
    
#     # Center line
#     plt.axhline(y=320, color='red', linestyle='--', linewidth=1.5, alpha=0.6)
#     plt.xlim([0, 640])
#     plt.ylim([0, 640])
#     plt.gca().invert_yaxis()
#     plt.xlabel('X (pixels)', fontsize=12, weight='bold')
#     plt.ylabel('Y (pixels)', fontsize=12, weight='bold')
    
#     # Concise title
#     plt.title(f'Buffer Edges: {link_id} | {side}', fontsize=13, weight='bold')
#     plt.grid(True, alpha=0.3)
    
#     plot_path = os.path.join(save_dir, "buffer_edges.jpg")
#     plt.savefig(plot_path, bbox_inches='tight', pad_inches=0, dpi=150)
#     plt.close()
    
#     print(f"✅ Buffer visualization saved: {plot_path}")
    
#     # Print summary (console only, no labels on the figure)
#     print(f"\n✅ Buffer Zone Edge Summary for {link_id} | {side}:")
#     print(summary)
    
#     # Check if edges are touching
#     if avg_distance < proximity_threshold:
#         print(f"✅ Edges are touching (distance < {proximity_threshold}px). No buffer exists.")
#         return None
    
#     # Calculate buffer width
#     T_init_sidewalk = 8 if p_10_sidewalk < 0 else 13
#     T_init_road = 8 if p_10_road < 0 else 13
    
#     T_sol_sidewalk = fsolve(equations_bottom, T_init_sidewalk, args=(p_0_sidewalk, p_10_sidewalk))
#     T_sol_road = fsolve(equations_top, T_init_road, args=(p_0_road, p_10_road))
    
#     print(f"Target Pitch (Sidewalk Bottom) [{link_id} | {side}]: {T_sol_sidewalk}")
#     print(f"Target Pitch (Road Top) [{link_id} | {side}]: {T_sol_road}")
    
#     T_sidewalk = T_sol_sidewalk[0]
#     T_road = T_sol_road[0]
    
#     cot_T_sidewalk = 1 / np.tan(np.radians(T_sidewalk))
#     cot_T_road = 1 / np.tan(np.radians(T_road))
    
#     buffer_width = 2.5 * (cot_T_sidewalk - cot_T_road)
    
#     if buffer_width < 0:
#         print(f"⚠️ Calculated negative buffer width: {buffer_width:.2f}m")
#         return None
    
#     print(f"✅ Estimated Buffer Width ({link_id} | {side}): {buffer_width:.2f}m")
    
#     return buffer_width

def _plot_buffer_edges(edges_with_distances, save_dir, link_id, side):
    """Helper to draw buffer_edges.jpg from edges_with_distances."""
    plt.figure(figsize=(12, 10))

    matched_clusters = sorted(edges_with_distances['cluster'].unique())

    for cluster in matched_clusters:
        cluster_data = edges_with_distances[edges_with_distances['cluster'] == cluster]

        for case in sorted(cluster_data['case'].unique()):
            pitch_data = cluster_data[cluster_data['case'] == case]

            sidewalk_edge = pitch_data[pitch_data['type'] == 'bottom']
            road_edge = pitch_data[pitch_data['type'] == 'top']

            linestyle = '--' if case == 0 else '-'
            alpha = 0.7

            # Sidewalk: blue (0°), sky blue (-10°)
            if not sidewalk_edge.empty:
                sw_row = sidewalk_edge.iloc[0]
                sw_color = 'blue' if case == 0 else 'skyblue'
                plt.plot(
                    [sw_row['x1'], sw_row['x2']],
                    [sw_row['y1'], sw_row['y2']],
                    color=sw_color,
                    linestyle=linestyle,
                    linewidth=3,
                    alpha=alpha,
                )

            # Road: red (0°), orange (-10°)
            if not road_edge.empty:
                rd_row = road_edge.iloc[0]
                rd_color = 'red' if case == 0 else 'orange'
                plt.plot(
                    [rd_row['x1'], rd_row['x2']],
                    [rd_row['y1'], rd_row['y2']],
                    color=rd_color,
                    linestyle=linestyle,
                    linewidth=3,
                    alpha=alpha,
                )

    plt.axhline(y=320, color='red', linestyle='--', linewidth=1.5, alpha=0.6)
    plt.xlim([0, 640])
    plt.ylim([0, 640])
    plt.gca().invert_yaxis()
    plt.xlabel('X (pixels)', fontsize=12, weight='bold')
    plt.ylabel('Y (pixels)', fontsize=12, weight='bold')
    plt.title(f'Buffer Edges: {link_id} | {side}', fontsize=13, weight='bold')
    plt.grid(True, alpha=0.3)

    plot_path = os.path.join(save_dir, "buffer_edges.jpg")
    plt.savefig(plot_path, bbox_inches='tight', pad_inches=0, dpi=150)
    plt.close()

    print(f"✅ Buffer visualization saved: {plot_path}")

def calculate_buffer_width(combined_df, save_dir, link_id=None, side=None,
                           proximity_threshold=10,
                           alignment_threshold=5,
                           alignment_ratio_threshold=0.2):
    """
    Calculate street buffer width between sidewalk bottom and road top edges.

    Logic:
      1. Compute per-cluster, per-pitch gaps between sidewalk bottom and road top
         using dist_central from add_distances().
      2. At pitch 0, if more than `alignment_ratio_threshold` of clusters
         have gap < `alignment_threshold` pixels, classify this location as
         having NO street buffer and return None.
      3. Otherwise, proceed with geometric buffer-width calculation.
    """
    # Separate sidewalk bottom and road top
    sidewalk_bottom = combined_df[combined_df['type'] == 'bottom'].copy()
    road_top = combined_df[combined_df['type'] == 'bottom_road'].copy()

    if sidewalk_bottom.empty or road_top.empty:
        print(f"⚠️ Missing sidewalk bottom or road top edges for {link_id} | {side}")
        return None

    # Rename road type to 'top' for distance calculation logic
    road_top['type'] = 'top'

    # Combine and calculate distances from image center
    edges_df = pd.concat([sidewalk_bottom, road_top], ignore_index=True)
    edges_with_distances = add_distances(edges_df)

    # ---------- NEW: cluster-level alignment check ----------
    # Pivot to get dist_central for sidewalk bottom and road top per (cluster, case)
    cluster_case = (
        edges_with_distances
        .pivot_table(
            index=['cluster', 'case'],
            columns='type',
            values='dist_central',
            aggfunc='mean'
        )
        .reset_index()
    )

    # Keep only rows where both sidewalk bottom and road top exist
    cluster_case = cluster_case.dropna(subset=['bottom', 'top'], how='any')

    # Focus on pitch 0 (case == 0) for the alignment frequency rule
    case0 = cluster_case[cluster_case['case'] == 0].copy()
    num_clusters_case0 = len(case0)

    if num_clusters_case0 > 0:
        case0['gap'] = (case0['bottom'] - case0['top']).abs()
        aligned_count = (case0['gap'] < alignment_threshold).sum()
        aligned_ratio = aligned_count / num_clusters_case0

        print(f"[{link_id} | {side}] pitch 0°: "
              f"{aligned_count}/{num_clusters_case0} clusters "
              f"({aligned_ratio:.1%}) have gap < {alignment_threshold}px")

        # If more than X% of clusters have nearly touching edges → no buffer
        if aligned_ratio >= alignment_ratio_threshold:
            print("➡️  Classified as NO STREET BUFFER based on alignment frequency rule.")
            # Still save the visualization, then return None
            _plot_buffer_edges(edges_with_distances, save_dir, link_id, side)
            return None
    else:
        print(f"[{link_id} | {side}] No valid clusters at pitch 0° for alignment check.")

    # ---------- Existing summary for geometric width ----------
    summary = edges_with_distances.groupby(['case', 'type'])['dist_central'].mean().unstack()

    try:
        p_0_sidewalk = summary.loc[0, 'bottom']
        p_10_sidewalk = summary.loc[-10, 'bottom']
        p_0_road = summary.loc[0, 'top']
        p_10_road = summary.loc[-10, 'top']
    except KeyError:
        print("⚠️ Missing edge data for pitch=0 or pitch=-10")
        return None

    # Calculate average distance between edges
    avg_distance_p0 = abs(p_0_sidewalk - p_0_road)
    avg_distance_p10 = abs(p_10_sidewalk - p_10_road)
    avg_distance = (avg_distance_p0 + avg_distance_p10) / 2

    # Draw visualization (using a helper for neatness)
    _plot_buffer_edges(edges_with_distances, save_dir, link_id, side)

    # If global average distance across pitches is very small → treat as no buffer
    if avg_distance < proximity_threshold:
        print(f"✅ Edges are touching on average (distance < {proximity_threshold}px). No buffer exists.")
        return None

    # ---------- Geometric buffer-width calculation ----------
    T_init_sidewalk = 8 if p_10_sidewalk < 0 else 13
    T_init_road = 8 if p_10_road < 0 else 13

    T_sol_sidewalk = fsolve(equations_bottom, T_init_sidewalk,
                            args=(p_0_sidewalk, p_10_sidewalk))
    T_sol_road = fsolve(equations_top, T_init_road,
                        args=(p_0_road, p_10_road))

    print(f"Target Pitch (Sidewalk Bottom) [{link_id} | {side}]: {T_sol_sidewalk}")
    print(f"Target Pitch (Road Top) [{link_id} | {side}]: {T_sol_road}")

    T_sidewalk = T_sol_sidewalk[0]
    T_road = T_sol_road[0]

    cot_T_sidewalk = 1 / np.tan(np.radians(T_sidewalk))
    cot_T_road = 1 / np.tan(np.radians(T_road))

    buffer_width = 2.5 * (cot_T_sidewalk - cot_T_road)

    if buffer_width < 0:
        print(f"⚠️ Calculated negative buffer width: {buffer_width:.2f}m")
        return None

    print(f"✅ Estimated Buffer Width ({link_id} | {side}): {buffer_width:.2f}m")
    return buffer_width

