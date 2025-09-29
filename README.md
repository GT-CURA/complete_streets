# Overview
This repository contains the code and datasets used to load locations for evaluating the Complete Street Score, identify and measure eight key Complete Street elements, and assign weights to each element using LLM/NLP techniques.

Diagram #1

Please note, you will require different conda environment to identify ~~~ for the use of Computer Vision. We recommend you to use specific you may need,,, We hope to make this as a package but, since it integrates several steps and funcitons, can't make it :(

# Quick Start
## 1. Create ~~~ [step1_preprocssing]
You can put multiple interested points at the same time either by, make sure 

## 2. Collect attributes of elements [step2_elements]
There are eight different elements meaning eight subfolders under step2_elements folder. You can use the process you may want to collect. No need to run all those codes unless you have alternate datasets. For example, if you know the types and locations of bike lane in your interested area, then skip it!. 

Each element will return its own unique csv that contains attribute so please follow the instructions found in each folder.

## 3. Calculate the completeness score [step3_scoring]
As of you collect all eight elements (it's okay you skip some elements), you need to integrate the files into one and calculate the completeness score for each road segment using our metrics developed for evaluating completeness score based on various complete street design guide books. Of course, you can find out more details in the folder as well.

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
