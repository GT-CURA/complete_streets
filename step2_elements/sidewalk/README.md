# Automated Sidewalk Width Estimation

## 📍 Objective
This repository provides tools to estimate sidewalk width (in meters) using two Google Street View images captured at different camera pitch angles. It includes both an automated model and a manual annotation interface.
- Automated Tool: Detects sidewalk and estimates width using a semantic segmentation model (SegFormer) and Canny edge detection to identify top and bottom sidewalk edges. A geometric model then calculates the physical width based on images taken at two pitch angles (0° and -10°).
- Manual Annotation Tool: Provides an interface for users to manually mark sidewalk edges when the automated method fails to detect them accurately. This tool also estimates sidewalk width using the same geometric logic. More details and code are available in the `/manual_collection` directory.

- **Input:** A GeoJSON file of road segment points.  
- **Process:**  
  1. Downloads Google Street View images for each point at two camera pitches (0° and -10°).
  2. Runs a SegFormer semantic segmentation model to identify sidewalks in each image.
  3. Applies image processing to extract the top and bottom edges of the detected sidewalks.
  4. Uses the pixel coordinates of the edges from both pitches to solve a system of geometric equations.
- **Output:**  
  - A CSV file for each input point containing the estimated `width` and an `error_code`. 
  - All downloaded images, segmentation masks, and intermediate line-detection visualizations are saved locally in the `/outputs` directory.


## 📦 Features:
- **`POINT_EPSG4326.geojson`**
  Example input file (5 sample points in Atlanta). Replace with your own points of interest.

- **`sidewalk_env.yml`**  
  Conda environment file specifying dependencies and pinned versions for reproducible setup.
  
- **Python scripts** in `utils_automation`  
  Contains modularized Python scripts supporting the automated pipeline. The main workflow can be executed via main.py

- **`/manual_collection`**
  Includes guidance and scripts for manual labeling of sidewalk edges.

## 🚗 Quick Guide
1. **Install conda environment**
   ```bash
   conda env create -f sidewalk_env.yml
   conda activate sidewalk_env
   ```
    
2. **Set Up the Segmentation Model**
The pipeline uses a configuration and checkpoint from the OpenMMLab MMSegmentation repository. You must clone the repository and download the weights.

  1. Clone the `mmsegmentation` repository
   ```bash
   git clone https://github.com/open-mmlab/mmsegmentation.git
   ```

   2. Create a `checkpoints` directory inside it and download the model:
  ```bash
   # Navigate into the new folder
   cd mmsegmentation
   
   # Create the directory
   mkdir checkpoints
  
   # Download the weights into that directory
   wget -P checkpoints/ https://download.openmmlab.com/mmsegmentation/v0.5/segformer/segformer_mit-b5_8x1_1024x1024_160k_cityscapes/segformer_mit-b5_8x1_1024x1024_160k_cityscapes_20211206_072934-87a052ec.pth
   ```

3. **Prepare input data**
  - Place your road segment GeoJSON file (generated via step1_loader) in the working directory, or use the provided toy dataset for testing.
  - Open `config.py` and edit the following variables:
    - [Line 6] Enter your Google API Key to allow imagery downloads.
    - [Line 10, 11] Verify that these paths correctly point to the files inside the `mmsegmentation` directory you just cloned.
    - [Line 18] Set the path where you want to save all outputs.

   
4. **Run the Python script**
Execute the main script from your terminal. The program will process each link_id from your GeoJSON sequentially.
```bash
python main.py
```

## 🔎 Descriptions
For details regarding the methodology please find the [paper](https://doi.org/10.1177/23998083251369602).

### References
If you use this model, please cite the following paper: 

```bibtex
@article{your_article,
  title   = {A novel approach for estimating sidewalk width from street view images and computer vision},
  author  = {Lieu, S. J., & Guhathakurta, S.},
  journal = {Environment and Planning B: Urban Analytics and City Science},
  year    = {2025}
}
