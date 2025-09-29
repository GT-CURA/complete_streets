This repository contains the code and example datasets for evaluating the Complete Street Score. 
The workflow identifies and measures eight key Complete Street elements, then integrates them into a composite score using metrics derived from complete street design guidelines.

Diagram #1

⚠️ Note: Some elements (e.g., street parking, sidewalk) require specialized conda environments with computer vision dependencies. Each element folder includes its own environment.yml. You only need to install and run the environments relevant to your use case.

We plan to release this as a Python package in the future. For now, the project is organized into modular steps that can be run independently or combined into a full pipeline.

# ✨ Features

- Modular design with three main steps:
    - Preprocess input points to generate point and line representations of the target road segments
    - Collection of eight element inventories
    - Integration into a final Complete Street Score
- Flexible: skip elements if you already have alternate datasets
- Sample inputs and outputs for quick testing

# 🚀 Quick Guide with Example
## 1. Create base road segment data (step1_preprocssing)
Provide one or more points of interest (lat/lon). The script generates the followings with two different projections:
Points along the road segment
Corresponding line representations

Example:


## 2. Collect element attributes (step2_elements)
There are eight element folders under step2_elements/.
Each contains its own workflow and environment:

Run the scripts for the elements you want to measure.

Skip elements if you already have equivalent data (e.g., if your city provides a bike lane shapefile).

Each element produces a CSV describing its attributes for each road segment.
Instructions are included in each folder.

## 3. Calculate the completeness score [step3_scoring]
Once you have collected outputs (from all or some elements), integrate them and calculate the Complete Street Score:

The score reflects segment-level completeness, following metrics derived from established design guidebooks.

# 📂 Repository Structure
```
complete-street/
│
├── README.md # High-level description, workflow diagram, quickstart
├── LICENSE
├── environment.yml
│
├── inputs/                   # Example input files (toy data, not real study area)
│   ├── amenities_test.geojson
│   ├── GTFS_test
│   └── sample_points.geojson
│
├── outputs/                  # Example outputs (toy outputs for demonstration)
│   ├── step1_preprocessing/
│   │   ├── POINT_EPSG4326.geojson
│   │   ├── LINE_EPSG4326.geojson
│   │   ├── POINT_UTMlocal.geojson
│   │   └── LINE_UTMlocal.geojson
│   ├── step2_elements/
│   │   ├── amenities.csv
│   │   ├── bike_lane.csv
│   │   ├── median.csv
│   │   ├── sidewalk.csv
│   │   ├── street_buffer.csv
│   │   ├── street_parking.csv
│   │   ├── transit_stop.csv
│   │   └── vehicular_road.csv
│   └── step3_scoring/
│       └── complete_score.csv
│
│
│
├── step1_preprocessing/      # Code for generating 4 geojsons from user inputs
│   ├── generate_points_lines.py
│   └── README.md
│
├── step2_elements/           # Each element has its own folder + env
│   ├── bike_lane/
│   │   ├── environment_bike_lane.yml
│   │   ├── bike_lanes.py
│   │   ├── trained_model.pt
│   │   └── README.md
│   ├── sidewalk/
│   ├── crossings/
│   ├── greenery/
│   ├── lighting/
│   ├── benches/
│   ├── transit_access/
│   └── shade/
│
└── step3_scoring/            # Code to integrate 8 inventories + compute final score
    ├── environment.yml
    ├── integrate_inventories.py
    └── calculate_score.py
```

## Quick Guide
