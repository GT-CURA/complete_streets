# complete_streets
This repository contains the code and datasets used to load locations for evaluating the Complete Street Score, identify and measure eight key Complete Street elements, and assign weights to each element using LLM/NLP techniques.

## 📂 Repository Structure

complete-street/
│
├── README.md                 # High-level description, workflow diagram, quickstart
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
├── step3_scoring/            # Code to integrate 8 inventories + compute final score
│   ├── environment.yml
│   ├── integrate_inventories.py
│   └── calculate_score.py
│
└── utils/                    # Shared helper functions
    ├── geoutils.py
    ├── io.py
    └── viz.py
