import os
import warnings
import torch
import pandas as pd
import numpy as np

from config import API_KEY, OUTPUT_DIR, GEOJSON_PATH
from load_points import load_midpoints
from download_image import download_images_for_temp
from segmentation import load_segmentation_model, run_segmentation
from sidewalk_processing import process_sidewalk_edges, estimate_sidewalk_width

# Suppress PyTorch / Python warnings
warnings.filterwarnings("ignore")
torch._C._jit_set_profiling_mode(False)
torch._C._jit_set_profiling_executor(False)

# ==============================
# Parameters
# ==============================
PITCH_VALUES = [0, -10]   # Pitches we want
FOV = 70                  # Field of View (degrees)

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
        edge_results = {}
        error_map = {}
        
        for key, pixel_df in seg_results.items():
            link_id, side, panoid, pitch = key
            save_dir = os.path.dirname(results[key])

            lines_df, err = process_sidewalk_edges(pixel_df, results[key], save_dir, pitch)
            if lines_df is not None:
                edge_results[key] = lines_df
                error_map[(link_id, side)] = None
            else:
                error_map[(link_id, side)] = err


        # ------------------------------
        # Step 5: Combine results per side
        # ------------------------------
        print("\n⏳ Combining results per side...")
        width_results = {}
        error_results = {}
        
        grouped = pd.DataFrame(list(edge_results.keys()), columns=["link_id", "side", "panoid", "pitch"])

        for (lid, side), group in grouped.groupby(["link_id", "side"]):
            combined_lines = pd.DataFrame()
            for _, row in group.iterrows():
                key = (row["link_id"], row["side"], row["panoid"], row["pitch"])
                if key in edge_results:
                    lines_df = edge_results[key].copy()
                    lines_df["pitch"] = row["pitch"]
                    combined_lines = pd.concat([combined_lines, lines_df], ignore_index=True)

            if combined_lines.empty:
                if error_map.get((lid, side)) == 0:
                    width_results[(lid, side)] = 0  # no sidewalk → width=0
                    error_results[(lid, side)] = None
                else:
                    width_results[(lid, side)] = None
                    error_results[(lid, side)] = error_map.get((lid, side), 1)
                continue

            save_dir = os.path.dirname(results[(lid, side, row["panoid"], row["pitch"])])
            width = estimate_sidewalk_width(combined_lines, save_dir, link_id=lid, side=side)

            if width is None:
                width_results[(lid, side)] = None
                error_results[(lid, side)] = 3
            elif width < 0:
                width_results[(lid, side)] = None
                error_results[(lid, side)] = 4
            else:
                width_results[(lid, side)] = width
                error_results[(lid, side)] = None

        # ------------------------------
        # Step 6: Merge widths back into temp_gdf
        # ------------------------------
        temp_gdf["width"] = np.nan
        temp_gdf["error_code"] = None

        for idx, row in temp_gdf.iterrows():
            key = (row["link_id"], row["side"])
            width_val = width_results.get(key, None)
            err_val = error_results.get(key, None)

            if width_val is not None:
                temp_gdf.at[idx, "width"] = round(width_val, 2)
            elif width_val == 0:
                temp_gdf.at[idx, "width"] = 0
            else:
                temp_gdf.at[idx, "width"] = np.nan

            temp_gdf.at[idx, "error_code"] = err_val

        print(temp_gdf[["link_id", "side", "width", "error_code"]])

        # ------------------------------
        # Step 7: Save results per panoid
        # ------------------------------
        cols_to_keep = ["link_id", "point_id", "bearing", "side", "pano_id", "pano_lat", "pano_lon", "pano_heading", "pano_date", "width", "error_code"]

        panoid = temp_gdf["pano_id"].iloc[0]
        output_path = os.path.join(OUTPUT_DIR, f"{panoid}.csv")
        temp_gdf[cols_to_keep].to_csv(output_path, index=False)
        print(f"✅ Saved {output_path}")