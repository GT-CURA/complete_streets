import os
import warnings
import torch
import pandas as pd
import numpy as np

from config import API_KEY, OUTPUT_DIR, GEOJSON_PATH
from load_points import load_midpoints
from download_image import download_images_for_temp
from segmentation import load_segmentation_model, run_segmentation
from sidewalk_processing import process_sidewalk_edges
from road_processing import process_road_edges, filter_top_road_edge
from buffer_calculation import combine_sidewalk_and_road_edges, calculate_buffer_width

# Suppress PyTorch / Python warnings
warnings.filterwarnings("ignore")
torch._C._jit_set_profiling_mode(False)
torch._C._jit_set_profiling_executor(False)

# ==============================
# Parameters
# ==============================
PITCH_VALUES = [0, -10]   # Pitches we want
FOV = 80                  # Field of View (degrees)

# ==============================
# Main Entry
# ==============================
if __name__ == "__main__":
    # ------------------------------
    # Step 0: Load candidate points
    # ------------------------------
    print("⏳ Loading midpoints...")
    link_groups = load_midpoints(GEOJSON_PATH)

    # ------------------------------
    # Step 1: Load segmentation model once
    # ------------------------------
    print("\n⏳ Loading segmentation model...")
    model = load_segmentation_model()

    # ------------------------------
    # Process each link_id separately
    # ------------------------------
    for link_id, temp_gdf in link_groups.items():
        print(f"\n=== Processing {link_id} ({len(temp_gdf)} rows) ===")

        # ------------------------------
        # Step 2: Download Street View images
        # ------------------------------
        print("\n⏳ Downloading Street View images...")
        results = download_images_for_temp(temp_gdf, pitch_values=PITCH_VALUES, fov=FOV)

        # ------------------------------
        # Step 3: Run segmentation
        # ------------------------------
        print("\n⏳ Running segmentation on downloaded images...")
        seg_results = {}
        for key, img_path in results.items():
            link_id, side, panoid, pitch = key
            save_dir = os.path.dirname(img_path)

            pixel_df = run_segmentation(model, img_path, save_dir)
            if pixel_df is None or pixel_df.empty:
                print(f"⚠️ Skipping segmentation for {img_path} (empty result).")
                continue

            seg_results[key] = pixel_df
            print(f"✅ Segmentation done for {img_path}")

        print(f"\n🎉 Total images segmented: {len(seg_results)}")

        # ------------------------------
        # Step 4: Extract sidewalk edges
        # ------------------------------
        print("\n⏳ Detecting sidewalk edges...")
        sidewalk_edge_results = {}
        sidewalk_error_map = {}
        
        for key, pixel_df in seg_results.items():
            link_id, side, panoid, pitch = key
            save_dir = os.path.dirname(results[key])

            lines_df, err = process_sidewalk_edges(pixel_df, results[key], save_dir, pitch)
            if lines_df is not None:
                sidewalk_edge_results[key] = lines_df
                sidewalk_error_map[(link_id, side)] = None
            else:
                sidewalk_error_map[(link_id, side)] = err

        # ------------------------------
        # Step 5: Extract road edges
        # ------------------------------
        print("\n⏳ Detecting road edges...")
        road_edge_results = {}
        road_error_map = {}
        
        for key, pixel_df in seg_results.items():
            link_id, side, panoid, pitch = key
            save_dir = os.path.dirname(results[key])

            road_lines_df, err = process_road_edges(pixel_df, results[key], save_dir, pitch)
            if road_lines_df is not None:
                # Filter to keep only top edge
                road_top_df = filter_top_road_edge(road_lines_df)
                road_edge_results[key] = road_top_df
                road_error_map[(link_id, side)] = None
            else:
                road_error_map[(link_id, side)] = err

        # ------------------------------
        # Step 6: Calculate buffer widths per side
        # ------------------------------
        print("\n⏳ Calculating buffer widths...")
        buffer_width_results = {}
        buffer_error_results = {}
        
        # Create grouped dataframe for edges that exist
        if sidewalk_edge_results:
            edge_grouped = pd.DataFrame(list(sidewalk_edge_results.keys()), 
                                       columns=["link_id", "side", "panoid", "pitch"])
            
            for (lid, side), group in edge_grouped.groupby(["link_id", "side"]):
                # Combine sidewalk edges (with top/bottom labels)
                combined_sidewalk = pd.DataFrame()
                combined_road = pd.DataFrame()
                
                for _, row in group.iterrows():
                    key = (row["link_id"], row["side"], row["panoid"], row["pitch"])
                    
                    # Get sidewalk edges
                    if key in sidewalk_edge_results:
                        sw_df = sidewalk_edge_results[key].copy()
                        sw_df["pitch"] = row["pitch"]
                        combined_sidewalk = pd.concat([combined_sidewalk, sw_df], ignore_index=True)
                    
                    # Get road edges
                    if key in road_edge_results:
                        rd_df = road_edge_results[key].copy()
                        rd_df["pitch"] = row["pitch"]
                        combined_road = pd.concat([combined_road, rd_df], ignore_index=True)
                
                # Check if we have both sidewalk and road data
                if combined_sidewalk.empty or combined_road.empty:
                    buffer_width_results[(lid, side)] = None
                    
                    if combined_sidewalk.empty and combined_road.empty:
                        buffer_error_results[(lid, side)] = 5  # Both missing
                    elif combined_sidewalk.empty:
                        buffer_error_results[(lid, side)] = 6  # Sidewalk missing
                    else:
                        buffer_error_results[(lid, side)] = 7  # Road missing
                    continue
                
                # Need to assign top/bottom to sidewalk edges first
                from image_processing_c import assign_top_or_bottom_and_filter
                
                combined_sidewalk_typed = assign_top_or_bottom_and_filter(combined_sidewalk)

                first = group.iloc[0]
                img_key = (first["link_id"], first["side"], first["panoid"], first["pitch"])
                save_dir = os.path.dirname(results[img_key])
                
                # Combine sidewalk bottom with road top
                combined_for_buffer = combine_sidewalk_and_road_edges(
                    combined_sidewalk_typed, 
                    combined_road,
                    save_dir=save_dir,      # ADD THIS
                    link_id=lid,   # ADD THIS
                    side=side      # ADD THIS
                )
                        
                if combined_for_buffer.empty:
                    buffer_width_results[(lid, side)] = None
                    buffer_error_results[(lid, side)] = None  # treat as "no buffer info"
                    continue
                
                buffer_width = calculate_buffer_width(
                    combined_for_buffer, 
                    save_dir=save_dir, 
                    link_id=lid, 
                    side=side
                )
                
                if buffer_width is None:
                    buffer_width_results[(lid, side)] = None  # No buffer (edges touching)
                    buffer_error_results[(lid, side)] = None  # Not an error, just no buffer
                elif buffer_width < 0:
                    buffer_width_results[(lid, side)] = None
                    buffer_error_results[(lid, side)] = 8  # Negative width
                else:
                    buffer_width_results[(lid, side)] = buffer_width
                    buffer_error_results[(lid, side)] = None

        # ------------------------------
        # Step 7: Merge buffer widths into temp_gdf
        # ------------------------------
        temp_gdf["buffer_width"] = np.nan
        temp_gdf["buffer_error_code"] = None

        for idx, row in temp_gdf.iterrows():
            key = (row["link_id"], row["side"])
        
            buffer_val = buffer_width_results.get(key, None)
            buffer_err_val = buffer_error_results.get(key, None)
        
            sidewalk_err = sidewalk_error_map.get(key, None)
            road_err = road_error_map.get(key, None)
        
            final_err_code = buffer_err_val
        
            # 1) If buffer_error_results already has a code (5,6,7,8...),
            if buffer_err_val is not None:
                temp_gdf.at[idx, "buffer_width"] = np.nan
        
            # 2) Else, if detection failed (sidewalk or road error),
            elif (sidewalk_err is not None) or (road_err is not None):
                temp_gdf.at[idx, "buffer_width"] = np.nan
        
                if final_err_code is None:
                    final_err_code = sidewalk_err if sidewalk_err is not None else road_err
        
            # 3) No errors anywhere → detection OK
            else:
                if buffer_val is None:
                    # Edges detected, but classified as NO STREET BUFFER
                    temp_gdf.at[idx, "buffer_width"] = "None"
                else:
                    temp_gdf.at[idx, "buffer_width"] = round(buffer_val, 2)
        
            temp_gdf.at[idx, "buffer_error_code"] = final_err_code



        print("\n" + "="*60)
        print(temp_gdf[["link_id", "side", "buffer_width", "buffer_error_code"]])
        print("="*60)

        # ------------------------------
        # Step 8: Save results per panoid
        # ------------------------------
        cols_to_keep = [
            "link_id", "point_id", "bearing", "side", "pano_id", 
            "pano_lat", "pano_lon", "pano_heading", "pano_date", 
            "buffer_width", "buffer_error_code"
        ]

        panoid = temp_gdf["pano_id"].iloc[0]
        output_path = os.path.join(OUTPUT_DIR, f"{panoid}.csv")
        temp_gdf[cols_to_keep].to_csv(output_path, index=False)
        print(f"\n✅ Saved {output_path}")
        
        # Print error code legend
        # print("\n📋 Buffer Error Code Legend:")
        # print("  5 = Both sidewalk and road edges missing")
        # print("  6 = Sidewalk edges missing")
        # print("  7 = Road edges missing")
        # print("  8 = Negative buffer width calculated")
        # print("  None (no error) = Either buffer exists OR edges touching (no buffer)")
        # print("  buffer_width=None + buffer_error_code=None → Edges are touching (no buffer)")
        # print("  buffer_width=value + buffer_error_code=None → Buffer exists")