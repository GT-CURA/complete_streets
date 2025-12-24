## 📍 Objective
This repository generates spatial inputs used in downstream analyses in `step2_elements` for collecting Complete Street element presence and attributes.

The code (`generate_points_lines.ipynb`) prepares a set of **line** and **point geometries** that:
- Represent road segments within a user-defined study area.
- Represent regularly spaced coordinates for downloading and analyzing Google Street View imagery 

Applied methods will depend on whether each road segment is a single or a dual carriageway.
- **Single** carriageway: A road with a single continuous surface carrying traffic in both directions, without a median separating flows
- **Dual** carriageway: A road where opposing traffic directions are separated by a median
  
<p align="left"> <img src="fig/fig1.png" width="640" alt="Road Segment Point Sampling Workflow"> </p>

### Input: 
A GeoJSON file containing either:
  - Road geometries (type: `LineString`) - `YOUR_ROADS.geojson` or
  - A study area boundary (type: `Polygon`) - `YOUR_STUDY_AREA.geojson`

### Output:
  - A GeoJSON file of processed road segment geometries (`LineString`), named `LINES_EPSG4326` by default.
  - A GeoJSON file of regularly spaced sampling points with valid GSV panorama locations (`Point`), named `POINTS_EPSG4326` by default.
  
<br>
<br>

## Workflow 
### 1. Load Spatial Data
- Import a GeoJSON file containing road linestrings or a study area polygon.

### 2. Clean and Filter Road Network
- Keep relevant road types according to the `highway` hierarchy in OSM (e.g., primary, secondary, residential).
- Reproject data to a projected CRS (e.g., EPSG:32616 in the Atlanta Metropolitan Region) for distance-based calculations.

### 3. Segment Roads into Uniform Lengths
- For long road geometries, extract a representative 30-meter segment from the center of each road.

### 4. Generate Sample Points Along Segments
- Generate points at 5-meter intervals along each road segment.
- Query the Google Street View Metadata API to retrieve valid panorama locations.
- Deduplicate the points and save ones with unique geographical coordinates
- Assign unique `point_id`s for the filtered points. These points will be in a 10-meter interval on average.

### 5. Export Results
- Save processed road segments and sampling points for use in subsequent element-level workflows.

<br>
<br>

## 🚗 Quick Guide
### 1. Install the Conda Environment
  ```bash
  conda env create -f loader_env.yaml
  conda activate loader_env
  unset PYTHONPATH  # avoids PROJ/GDAL CRS errors

  # Optional: To use jupyter notebook, execute the following
  conda install -c conda-forge jupyterlab ipykernel
  python -m ipykernel install --user --name loader_env --display-name "Python (loader_env)"
  ```

### 2. Run the Workflow
#### 1. Open Jupyter Lab:
  ```bash
  jupyter lab
  ```
 
#### 2. Run the following script
  ```bash
  generate_points_lines.ipynb
  ```
