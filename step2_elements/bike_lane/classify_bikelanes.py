######################################
# ✅ Please change the followings
"""The directory where this code file is located. Be sure that the input location file and classifcation model's checkpoint file are also in this directory"""
WORK_DIR = ""

"""Your Google API key that enables downloading the street view imagery and satellite imagery"""
"""You should enable your key to 'Street View Static API' and 'Map Tiles API' in your Google Cloud project"""
API_KEY = "YOUR_API_KEY"


######################################
#### ---- 📌 Block 0 — Setup ---- ####
import os
import geopandas as gpd
import pandas as pd
from tqdm import tqdm

CHECKPOINT_PATH = os.path.join(WORK_DIR, "bike_lane_classification.pt")
POINTS_FILE = os.path.join(WORK_DIR, "POINT_EPSG4326.geojson")

# Check if checkpoint file exists
if os.path.exists(CHECKPOINT_PATH):
    print(f"✅ Checkpoint file found: {CHECKPOINT_PATH}")
else:
    raise FileNotFoundError(f"❌ Checkpoint file not found: {CHECKPOINT_PATH}")

# Check if location input file exists and load
if os.path.exists(POINTS_FILE):
    points_gdf = gpd.read_file(POINTS_FILE)
    print(f"✅ GeoDataFrame successfully loaded with {len(points_gdf)} records.")
else:
    raise FileNotFoundError(f"❌ GeoJSON file not found: {POINTS_FILE}")


###########################################################
#### ---- 📌 Block 1 — Helpers to fetch GSV & SAT ---- ####
import requests
from PIL import Image
from io import BytesIO

# Filter midpoint +  one side
points_gdf = points_gdf.query("is_midpoint == True and side == 'side1'")
print(f"✅ Loaded {len(points_gdf)} points after filtering")

# Genearte subfolders to store images and outputs
os.makedirs(os.path.join(WORK_DIR, "images"), exist_ok=True)
os.makedirs(os.path.join(WORK_DIR, "outputs"), exist_ok=True)

save_dir = os.path.join(WORK_DIR, "images")
output_dir = os.path.join(WORK_DIR, "outputs")

# Function to download street view imagery using pano_id
def download_gsv(pano_id, heading, fov=120, pitch=-30, fname="temp.jpg"):
    url = (
        "https://maps.googleapis.com/maps/api/streetview"
        f"?size=640x640&pano={pano_id}&heading={heading}"
        f"&fov={fov}&pitch={pitch}&source=outdoor&key={API_KEY}"
    )
    r = requests.get(url)
    if r.status_code == 200:
        with open(fname, "wb") as f:
            f.write(r.content)
        return fname
    else:
        print(f"⚠️ Failed GSV: {r.status_code}")
        return None

# Function to download satellite imagery using location info
def download_sat(lat, lon, zoom=21, fname="temp.jpg"):
    url = (
        "https://maps.googleapis.com/maps/api/staticmap"
        f"?center={lat},{lon}&zoom={zoom}&size=640x640"
        f"&maptype=satellite&key={API_KEY}"
    )
    r = requests.get(url)
    if r.status_code == 200:
        with open(fname, "wb") as f:
            f.write(r.content)
        return fname
    else:
        print(f"⚠️ Failed SAT: {r.status_code}")
        return None

# Download images for all points
results = []
for idx, row in tqdm(points_gdf.iterrows(), total=len(points_gdf)):
    pano_id = row["pano_id"]
    seg_id = str(row["link_id"])
    lat, lon = row.geometry.y, row.geometry.x
    heading = row["pano_heading"]

    # Opposite heading (keep within 0–360)
    opp_heading = (heading + 180) % 360

    f_gsv1 = os.path.join(save_dir, f"{seg_id}_MID_GSV1.jpg")
    f_gsv2 = os.path.join(save_dir, f"{seg_id}_MID_GSV2.jpg")
    f_sat  = os.path.join(save_dir, f"{seg_id}_SAT.jpg")

    download_gsv(pano_id, heading, fname=f_gsv1)
    download_gsv(pano_id, opp_heading, fname=f_gsv2)
    download_sat(lat, lon, fname=f_sat)

    results.append({
        "segment_id": seg_id,
        "lat": lat, "lon": lon,
        "GSV1": f_gsv1, "GSV2": f_gsv2, "SAT": f_sat
    })

print(f"✅ Download complete. {len(results)} segments saved to {save_dir}")


######################################################
#### ---- 📌 Block 2 — Load model checkpoint ---- ####
import torch
from torch import nn
from transformers import SwinModel

# Model Definition
class SwinSingleViewHier(nn.Module):
    def __init__(self, model_name="microsoft/swin-large-patch4-window12-384"):
        super().__init__()
        self.backbone = SwinModel.from_pretrained(model_name)
        for n, p in self.backbone.named_parameters():
            p.requires_grad = False
            if "layers.2" in n or "layers.3" in n:
                p.requires_grad = True
        hidden = self.backbone.config.hidden_size
        self.head_presence = nn.Sequential(
            nn.Linear(hidden, 512), nn.ReLU(),
            nn.Linear(512, 2)    # 0=no-lane, 1=lane
        )
        self.head_type = nn.Sequential(
            nn.Linear(hidden, 512), nn.ReLU(),
            nn.Linear(512, 2)    # 0=designated, 1=protected
        )
    def forward(self, x):
        f = self.backbone(x).last_hidden_state.mean(dim=1)
        return self.head_presence(f), self.head_type(f)


# Fusion Layer
class WeightedDecisionFusionHier(nn.Module):
    def __init__(self):
        super().__init__()
        self.raw_w = nn.Parameter(torch.tensor([0.33, 0.33, 0.34], dtype=torch.float32))
        self.softmax = nn.Softmax(dim=0)
        self.dropout = nn.Dropout(p=0.2)
    def forward(self, p1, p2, p3, t1, t2, t3):
        w = self.softmax(self.raw_w)
        fused_presence = self.dropout(w[0]*p1 + w[1]*p2 + w[2]*p3)
        fused_type     = self.dropout(w[0]*t1 + w[1]*t2 + w[2]*t3)
        return fused_presence, fused_type
    @torch.no_grad()
    def weights(self):
        return self.softmax(self.raw_w).detach().cpu().numpy()

def load_bike_lane_model(checkpoint_path, device):
    model_gsv1 = SwinSingleViewHier().to(device)
    model_gsv2 = SwinSingleViewHier().to(device)
    model_sat  = SwinSingleViewHier().to(device)
    model_fusion = WeightedDecisionFusionHier().to(device)

    checkpoint = torch.load(checkpoint_path, map_location=device)
    print(f"✅ Loaded checkpoint: {checkpoint_path}")

    model_gsv1.load_state_dict(checkpoint["gsv1"])
    model_gsv2.load_state_dict(checkpoint["gsv2"])
    model_sat.load_state_dict(checkpoint["sat"])
    model_fusion.load_state_dict(checkpoint["fusion"])

    [m.eval() for m in [model_gsv1, model_gsv2, model_sat, model_fusion]]
    return model_gsv1, model_gsv2, model_sat, model_fusion

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
models = load_bike_lane_model(CHECKPOINT_PATH, device)


#########################################################
#### ---- 📌 Block 3 — Run classification model ---- ####
from torchvision import transforms

def apply_bike_lane_model(results, output_dir, models, device, input_size=384):
    model_gsv1, model_gsv2, model_sat, model_fusion = models
    transform = transforms.Compose([
        transforms.Resize((input_size, input_size)),
        transforms.ToTensor()
    ])
    label_map = {0: "No Bike Lane", 1: "Designated", 2: "Protected"}

    results_out = []
    for row in tqdm(results, total=len(results)):
        seg_id = row["segment_id"]
        try:
            f_gsv1, f_gsv2, f_sat = row["GSV1"], row["GSV2"], row["SAT"]

            img1 = transform(Image.open(f_gsv1).convert("RGB")).unsqueeze(0).to(device)
            img2 = transform(Image.open(f_gsv2).convert("RGB")).unsqueeze(0).to(device)
            img3 = transform(Image.open(f_sat).convert("RGB")).unsqueeze(0).to(device)

            with torch.no_grad():
                o1p, o1t = model_gsv1(img1)
                o2p, o2t = model_gsv2(img2)
                o3p, o3t = model_sat(img3)
                fused1, fused2 = model_fusion(o1p, o2p, o3p, o1t, o2t, o3t)

                preds1 = torch.argmax(fused1, dim=1)
                preds2 = torch.argmax(fused2, dim=1)
                final_preds = preds1.clone()
                final_preds[preds1 == 1] = preds2[preds1 == 1] + 1

                label_idx = int(final_preds.item())
                label_str = label_map[label_idx]

                probs1 = torch.softmax(fused1, dim=1).cpu().numpy()[0]
                probs2 = torch.softmax(fused2, dim=1).cpu().numpy()[0]

                if label_idx == 0:
                    prob = float(probs1[0])
                elif label_idx == 1:
                    prob = float(probs1[1] * probs2[0])
                else:
                    prob = float(probs1[1] * probs2[1])

            results_out.append({
                "segment_id": seg_id,
                "label": label_str,
                "probability": prob,
                "prob_no_bike": float(probs1[0]),
                "prob_designated": float(probs1[1] * probs2[0]),
                "prob_protected": float(probs1[1] * probs2[1]),
            })
        except Exception as e:
            print(f"⚠️ Failed inference for {seg_id}: {e}")
            continue

    results_df = pd.DataFrame(results_out)
    results_csv = os.path.join(output_dir, "bike_lane_predictions.csv")
    results_df.to_csv(results_csv, index=False)
    print(f"✅ Predictions saved: {results_csv}")
    return results_df

results_df = apply_bike_lane_model(results, output_dir, models, device)