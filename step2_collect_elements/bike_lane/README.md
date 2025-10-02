# Automated Bike Lane Detection and Classification

## 📍 Objective
This repository provides a **multimodal deep learning framework** to detect and classify bike lane infrastructure using **street view and satellite imagery**.

- **Input:** A GeoJSON file of road segment points.  
- **Process:**  
  1. Download Google Street View images (two opposing headings) and a satellite tile for each location.  
  2. Run a pretrained deep learning model
- **Output:**  
  - A CSV file of predictions including **segment_id**, **classification label** ('No Bike Lane', 'Designated', 'Protected'), and **confidence probabilities**.  
  - Downloaded images stored locally in `/images`.
  - Model outputs stored in `/outputs`.  


## 📦 Features:
- **`.pt`**  
  Pretrained model checkpoint (PyTorch). Includes separate backbones for each modality (Street View 1, Street View 2, Satellite) and a decision-level hierarchical fusion head.  

- **`bike_lane_env.yml`**  
  Conda environment specification with pinned package versions for reproducible setup.  

- **`/images/`**  
  Folder automatically generated to store downloaded Street View and satellite images.  

- **`/outputs/`**  
  Folder automatically generated to store final predictions (CSV files).  

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
  - Place your road segment GeoJSON file (generated via step1_loader) into the working directory
  - Open classify_bikelanes.py and edit:
    - [Line 4] Set the working directory where .py, .yml, .pt, and the GeoJSON file are stored.
    - [Line 8] Enter your Google API Key (enabled for Street View Static API and Map Tiles API) to allow imagery downloads.

3. **Run the Python script**
```bash
python classify_bikelanes.py
```

## 🔎 Descriptions


### References
If you use this code, please cite:
