# Automated Bike Lane Detection and Classification

## 📍 Objective
This repository provides a **multimodal deep learning framework** to detect and classify bike lane infrastructure using **street view and satellite imagery**.

- **Input:** A GeoJSON file of road segment points.  
- **Process:**  
  1. Download Google Street View images (two opposing headings) and a satellite tile for each location.  
  2. Run a pretrained deep learning model.
- **Output:**  
  - A CSV file of predictions including **segment_id**, **classification label** ('No Bike Lane', 'Designated', 'Protected'), and **confidence probabilities**.  
  - Downloaded images stored locally in `/images`.
  - Model outputs stored in `/outputs`.  


## 📦 Features:
- **`POINT_EPSG4326.geojson`**
  Example input file (5 sample points in Atlanta). Replace with your own points of interest.

- **`bike_lane_classification_min_fp16.pt`**  
  Pretrained model checkpoint (PyTorch) with separate backbones for each modality (Street View 1, Street View 2, Satellite). See *Download pretrained weights* below.

- **`bike_lane_env.yml`**  
  Conda environment specification with pinned package versions for reproducible setup.  

- **`/images/`**  
  Automatically created folder for downloaded Street View and satellite imagery. 

- **`/outputs/`**  
  Automatically created folder for storing classification results.  

- **Python scripts (`classify_bikelanes.py`)**  
  - *Block 0*: Setup and load input GeoJSON  
  - *Block 1*: Download GSV & satellite imagery  
  - *Block 2*: Load trained PyTorch model from checkpoint  
  - *Block 3*: Run classification and save outputs  


## 🚗 Quick Guide
1. **Install conda environment**
   ```bash
   conda env create -f bike_lane_env.yml
   conda activate bike_lane_env
   ```

2. **Prepare input data**
  - Place your road segment GeoJSON file (generated via step1_loader) in the working directory, or use the provided toy dataset for testing.
  - Open classify_bikelanes.py and edit:
    - [Line 4] Set the working directory where .py, .yml, .pt, and the GeoJSON file are stored.
    - [Line 8] Enter your Google API Key (enabled for Street View Static API and Map Tiles API) to allow imagery downloads.

3. **Download pretrained weights**
The script expects `bike_lane_classification_min_fp16.pt` in your working directory.
- Browser:
  Download from the Release asset:

  https://github.com/GT-CURA/complete_streets/releases/download/v0.1.0/bike_lane_classification_min_fp16.pt
  Then place it in your working directory

- Terminal
   ```bash
  # From your working directory (same folder as classify_bikelanes.py)
  curl -L \
  -o bike_lane_classification_min_fp16.pt \
  "https://github.com/GT-CURA/complete_streets/releases/download/v0.1.0/bike_lane_classification_min_fp16.pt"
  # or:
  # wget -O bike_lane_classification_min_fp16.pt \
  # "https://github.com/GT-CURA/complete_streets/releases/download/v0.1.0/bike_lane_classification_min_fp16.pt"
   ```
   
5. **Run the Python script**
```bash
python classify_bikelanes.py
```

## 🔎 Descriptions


### References
If you use this code, please cite:
