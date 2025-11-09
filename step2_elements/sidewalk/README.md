# Automated Sidewalk Width Estimation

## 📍 Objective
This repository provides tools to estimate sidewalk width (in meters) using two Google Street View images captured at different camera pitch angles. It includes both an automated model and a manual annotation tool.
- Automated Model: Uses a semantic segmentation model (SegFormer) to detect sidewalk pixels, then applies Canny edge detection to locate the top and bottom sidewalk edges. A simple geometric model converts pixel distances (from two pitch angles) into physical width.
- Manual Annotation Tool: A Jupyter-based interface for manually marking sidewalk edges when the automated pipeline fails or is uncertain. It uses the same geometric model to estimate width. Code and instructions are available in the `/manual_collection` directory.

### Input: 
A GeoJSON file of road segment points.  
### Process:  
  1. Download Google Street View images for each point at two pitches (0° and -10°).
  2. Run a SegFormer semantic segmentation model to identify sidewalks in each image.
  3. Extract top and bottom sidewalk edges from segmentation masks.
  4. Use pixel coordinates of the edges from both pitches to solve a of geometric system and estimate sidewalk width.
### Output:
  - A CSV file for each input point containing the estimated sidewalk `width` or `NaN` (representing failed or unreliable sidewalk detection).
  - All downloaded images, segmentation masks, and intermediate line-detection visualizations are saved locally in the `/outputs` directory.

<br>
<br>

## 📦 Features:
- **`POINT_EPSG4326.geojson`**  
  Example input file (5 sample points in Atlanta). You can replace this with your own GeoJSON of points along road segments derived from `step1_loader`.
  
- **`/utils_automation`**  
  Includes python modules that implement the automated pipeline. The main workflow can be executed via main.py.

- **`/outputs_automation`** *example output*  
  Directory containing downloaded images, segmentation masks, and estimated width outputs generated automatically when running the tool on the example input file.

- **`/manual_collection`**  
  Scripts and instructions for manual edge annotation of sidewalks.

<br>
<br>

## 🚗 Quick Guide
### 1. Load Semantic Segmentation Model
The semantic **segmentation model** used in this analysis is **SegFormer** [(Official Repo)](https://github.com/NVlabs/SegFormer), with both its configuration and pretrained checkpoint obtained from the OpenMMLab MMSegmentation repository. Before downloading the SegFormer weights, you must first install and verify MMSegmentation following the official [installation guide](https://github.com/open-mmlab/mmsegmentation/blob/main/docs/en/get_started.md). Once MMSegmentation is properly set up, download the SegFormer model checkpoint from the same repository. You are also welcome to experiment with other semantic segmentation models trained on the Cityscapes dataset if you wish to extend performance.

<br>

Below is an example setup on a machine that supports *PyTorch with CUDA 11.8*. If your hardware is different, adjust the PyTorch installation step using the official PyTorch instructions.

#### 1. Create and activate Conda environment
   ```bash   
   conda create --name sidewalk_width python=3.8 -y
   conda activate sidewalk_width
   ```
  
#### 2. Install PyTorch (GPU example with CUDA 11.8) <br>
For CUDA 11.8 on Linux:
  ```bash   
  conda install pytorch torchvision pytorch-cuda=11.8 -c pytorch -c nvidia
  
  # Quick check
  python -c "import torch; print(torch.cuda.is_available(), torch.version.cuda)"
  ```

#### 3. Install MMCV
  ```bash
  pip install fsspec
  pip install -U openmim
  mim install mmengine
  mim install "mmcv==2.2.0"
  ```
  
#### 4. Install MMSegmentation
  ```bash
  git clone -b main https://github.com/open-mmlab/mmsegmentation.git
  cd mmsegmentation
  pip install -v -e .
  ```

#### 5. Download SegFormer checkpoint <br>
Inside the `mmsegmentation` folder:
  ```bash   
  # Create the directory
  mkdir checkpoints

  # Download the weights of SegFormer into that directory
  wget -P checkpoints/ https://download.openmmlab.com/mmsegmentation/v0.5/segformer/segformer_mit-b5_8x1_1024x1024_160k_cityscapes/segformer_mit-b5_8x1_1024x1024_160k_cityscapes_20211206_072934-87a052ec.pth
  ```

<br>

### 2. Install Utility Dependencies
After successfully setting up the semantic segmentation model, install the following dependencies:
  ```bash
  conda install -c conda-forge pillow requests -y
  conda install -c conda-forge geopandas ftfy regex scikit-image
  ```

### 3. Prepare Input Data
- Place your road segment GeoJSON file (generated via step1_loader) in the working directory, or use the provided toy dataset for testing.
- Open `config.py` and edit the following variables:
  - [Line 6] Enter your Google API Key to allow imagery downloads.
  - [Line 9] Specify the directory path of your input data file (.geojson).
  - [Line 13, 14] Provide the correct paths to the segmentation configuration and checkpoint files within the `mmsegmentation` directory you cloned earlier.
  - [Line 21] Define the output directory where all generated files and images will be saved.

### 4. Run the Automated Pipeline
From the `utils_automation` directory, execute the main script from your terminal. The program will process each link_id from your GeoJSON sequentially.
  ```bash
  python main.py
  ```

*Note* If you see an error: `AssertionError: MMCV==2.2.0 is used but incompatible Please install mmcv>=2.0.0rc4` modify the file **mmsegmenation/mmseg/__init__.py** by changing: `MMCV_MAX = '2.2.0'` → `MMCV_MAX = '2.2.1'`

<br>
<br>

## 🔎 Descriptions
For details about the methodology, please find the [paper](https://doi.org/10.1177/23998083251369602).

<br>
<br>

### References
If you use this methodology or code, please cite: 

```bibtex
@article{lieu_guhathakurta_2025_sidewalk_width,
  title   = {A novel approach for estimating sidewalk width from street view images and computer vision},
  author  = {Lieu, S. J., & Guhathakurta, S.},
  journal = {Environment and Planning B: Urban Analytics and City Science},
  year    = {2025}
}
