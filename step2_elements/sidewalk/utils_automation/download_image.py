import os
import requests
from config import API_KEY, OUTPUT_DIR

def get_streetview_image(panoid, heading, fov, pitch, save_dir, side):
    """Download Google Street View image given panoid, heading, pitch, and side."""
    base_url = "https://maps.googleapis.com/maps/api/streetview"
    url = f"{base_url}?size=640x640&pano={panoid}&heading={heading}&fov={fov}&pitch={pitch}&source=outdoor&key={API_KEY}"

    # Folder first groups by panoid+heading
    folder_name = str(panoid)        # only panoid
    folder_path = os.path.join(save_dir, folder_name, side)
    os.makedirs(folder_path, exist_ok=True)

    filename = f"pitch{pitch}_heading{heading}.jpg"
    file_path = os.path.join(folder_path, filename)

    response = requests.get(url)
    if response.status_code == 200:
        with open(file_path, "wb") as file:
            file.write(response.content)
        return file_path
    else:
        print(f"Failed to download image (pitch={pitch}), Status Code: {response.status_code}")
        return None


def adjust_heading(pano_heading, bearing):
    """Adjust heading based on road bearing vs pano_heading."""
    diff = abs(pano_heading - bearing)
    diff = diff if diff <= 180 else 360 - diff  # shortest angular distance

    if diff <= 45 or diff >= 315:
        adjusted = pano_heading + 90
    else:
        adjusted = pano_heading - 90

    return adjusted % 360   # keep in [0, 360)


def download_images_for_temp(temp_gdf, pitch_values=[0, -10], fov=65, save_dir=OUTPUT_DIR):
    """Download images for each side (side1, side2) with adjusted headings."""
    all_results = {}

    for idx, row in temp_gdf.iterrows():
        panoid = row["pano_id"]
        pano_heading = row["pano_heading"]
        bearing = row["bearing"]
        side = row["side"]   # side1 or side2

        # Calculate diff to determine FOV
        diff = abs(pano_heading - bearing)
        diff = diff if diff <= 180 else 360 - diff
        
        # Set FOV based on diff condition
        if diff <= 45 or diff >= 315:
            current_fov = 95 
        else:
            current_fov = fov   

        heading = adjust_heading(pano_heading, bearing)

        # print(f"\n📍 Processing link_id={row['link_id']} | {side} | panoid={panoid} | heading={heading} | FOV={current_fov}")

        for pitch in pitch_values:
            img_path = get_streetview_image(
                panoid=panoid,
                heading=heading,
                fov=current_fov,
                pitch=pitch,
                save_dir=save_dir,
                side=side
            )
            if img_path:
                print(f"✅ Saved: {img_path}")
                all_results[(row["link_id"], side, panoid, pitch)] = img_path
            else:
                print(f"⚠️ Failed for panoid={panoid}, pitch={pitch}, side={side}")

    return all_results