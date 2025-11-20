# Loading Road Segments from OSM

## 📍 Objective
This repository (`generate_points_lines.ipynb`) provides tools to retrieve spatial inputs for use in downstream analyses in `step2_elements` of this Complete Streets project. 
<br>

Specifically, the codes prepare a set of **line** and **point geometries** that:
- Represent road segments within the area of your choice.
- Provide regularly spaced coordinates for downloading or analyzing Google Street View imagery 
<br>

Applied methods will depend on whether each road segment is a single or a dual carriageway.
- **Single** carriageway: A road that has a single continuous surface or strip for traffic travelling in both directions, with no central reservation or physical barrier to separate opposing flows
- **Dual** carriageway: A road where the traffic flowing in opposite directions is separated by a physical barrier or strip of land
<p align="center"> <img src="fig/fig1.png" width="500
" alt="Road Segment Point Sampling Workflow"> </p>

### Input: 
A GeoJSON file containing either:
  - Road linestrings (`YOUR_ROADS.geojson`) or
  - A study area polygon (`YOUR_STUDY_AREA.geojson`)
### Output:
  - A GeoJSON file for segmented road geometries (linestrings), named `LINES_EPSG4326` by default.
  - A GeoJSON file for sampled GSV PanoID locations (points), named `POINTS_EPSG4326` by default.
  
<br>
<br>

## Workflow 
### 1. Load Required Spatial Data
- Import a GeoJSON file containing road linestrings or a study area polygon.

### 2. Clean and Filter Road Network
- Keep relevant road types according to the `highway` hierarchy in OSM (e.g., primary, secondary, residential).
- Reproject data to a projected CRS (e.g., EPSG:32616 in the Atlanta Metropolitan Region) for distance-based calculations.

### 3. Segment Roads into Uniform Lengths
- Select a single 30-meter segment in the middle for long road geometries.

### 4. Generate Sample Points Along Segments
- Compute points at an equal interval of 5-meter along each segment’s geometry.
- Make a GSV metadata API call to retrieve the geographical coordinates (longitude, latitude) of each sampled point.
- Deduplicate the points and save ones with unique geographical coordinates
- Assign unique `point_id`s for the filtered points. These points will be in a 10-meter interval on average.

### 5. Export Results
- Save generated features for use in later workflows:

<br>
<br>

## 🚗 Quick Guide
### 1. Install Conda Environments
  ```bash
  conda env create -f loader_env.yaml
  conda activate loader_env
  unset PYTHONPATH  # avoids PROJ/GDAL CRS errors

  # Optional: To use jupyter notebook, execute the following
  conda install -c conda-forge jupyterlab ipykernel
  python -m ipykernel install --user --name loader_env --display-name "Python (loader_env)"
  ```

### 2. Run the Workflow
1. Open Jupyter Lab:
    ```bash
    jupyter lab
    ```
 
2. Run the following script 
  - generate_points_lines.ipynb