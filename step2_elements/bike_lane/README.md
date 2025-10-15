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

[▶️ Watch the demo (MP4)](fig/bike_lane_tutorial.mp4)

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
The pretrained model provided in this repository is the top-performing architecture identified in the research, achieving the highest classification accuracy (90.4%) and F1-score (0.871). It employs a multimodal approach that integrates ground-level and aerial perspectives to create a robust and accurate classification framework.

The model's architecture is defined by three key dimensions: a late-stage concatenation, decision-level fusion, and a hierarchical label structure.

<p align="center"> <img src="fig/overview_bike_lane.png" width="640" alt="Overview of the multimodal bike lane classification pipeline"> </p>

**Key Architectural Features:**
  - ***Input Modalities***: The model processes three co-located images for each road segment: two Google Street View images captured from opposite directions and one satellite image. All input images are resized to 384 × 384 pixels.
  - ***Feature Extraction***: Each of the three images is independently passed through its own parallel Swin Transformer (Swin-S) backbone to extract high-level feature representations. This late-stage approach allows each modality's features to be fully processed before integration.
  - ***Decision-Level Fusion***: Rather than combining feature vectors, this model fuses the predictions from each modality. Each of the three feature sets is passed to a separate classification head to produce independent predictions (logits). These logits are then aggregated using a learnable weighted average to produce a final, unified prediction.
  - ***Hierarchical Classification***: The model decomposes the classification task into a two-stage process to improve accuracy.
    - Presence Detection: The first stage determines if a bike lane of any type is present.
    - Type Classification: If a bike lane is detected, the second stage classifies it as either designated or protected.

For details on the training process and ablation studies across three architectural dimensions (concatenation stage, fusion strategy, and label structure) see the paper (link). The code and dataset used for training are available in the `train` subfolder.

### References
If you use this model, please cite the following paper:
