# Estimating Number of Vehicular Lanes

## 📍 Objective
This repository explains the process of estimating the **number of lanes** for each road segment using OpenStreetMap (OSM) data.  

The algorithm in `step1_loader/generate_points_lines.ipynb` retrieves road linestrings and determines the total number of lanes per segment by summing the OSM `lanes` attributes. Detail proceesses are described as follow.

<br>

### Input
The same input used in `generate_points_lines.ipynb`, typically a GeoJSON file containing:
  - Road LineString geometries (`YOUR_ROADS.geojson`) or
  - A study area polygon (`YOUR_STUDY_AREA.geojson`)
### Output
A CSV file showing the number of vehicular lanes for each road segment (`lanes_collapsed`)
  
<br>
<br>

## Workflow 
### 1. Download the OSM Road Network  
   - Retrieve nearby road geometries using **OSMnx** with a custom highway filter  
     (`"trunk|primary|secondary|tertiary|residential|unclassified"`).  
   - The function `graph_from_point()` builds a subgraph centered on each COI.  

### 2. Preprocess Network Data  
   - Compute directional bearings for each edge (`ox.bearing.add_edge_bearings`).  
   - Project the graph into an appropriate UTM CRS for spatial distance operations.  

### 3. Find Nearest Edges
   - Calculate Euclidean distance between each road edge and the COI.  
   - Keep the two closest edges (`edges_nearest`) as potential carriageway pairs.  

### 4. Determine Road Type 
   - If such pairs are found, classify the segment as a **dual carriageway**
      - a road that has a single continuous surface or strip for traffic travelling in both directions, with no central reservation or physical barrier to separate opposing flows
   - Otherwise, label the segement as a **single carriageway**
      - a road where the traffic flowing in opposite directions is separated by a physical barrier or strip of land
<p align="center"> <img src="fig/fig1.png" width="500
" alt="Road Segment Point Sampling Workflow"> </p>

### 5. Estimate Number of Lanes
   - Collapse and clean the OSM `lanes` attribute using the `collapse_lanes()` function.  
   - If two opposing one-way segments form a dual carriageway, **sum** their lane counts.  
   - If the `lanes` attribute is missing, assign a default value of 1.  
   - Store the result in a new column `lanes_collapsed`.  
### 6. Save
   - Save a new road segment record containing: `link_id`, `osmid`, `road_type`, `lanes_collapsed`, and `geometry`.


<br>
<br>

## 🚗 Quick Guide
Please refer to the [step1_loader README file](../../step1_loader/README.md)