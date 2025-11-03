## 📍 Objective
This repository provides a framework to evaluate accessibility to daily amenities (i.e., points of interests) for given road segments. It demonstrates how to derive a composite accessibility index that accounts for amenity density, amenity importance, and road length through four main steps.

- **Input:**
  1. A GeoJSON file of road segment points.
  2. CSV table defining amenity-type weights (based on NACIS codes and behavioral factors).
- **Process:**  
  1. Generate walksheds (reachable areas) around each road segment point.
  2. Collect daily points of interests (POIs) within each walksehd.
  3. Assign weighted values to POIs using standardized popularity, intensity, and operating hour metrics.
  4. Aggregate the weighted POIs into a composite accessibility score that relfects both POI density and road length
- **Output:**  
  - The composite accessibility score for each road segment.


## 📦 Features:
- **`POINT_EPSG4326.geojson`**
  Example input file (5 sample points in Atlanta). Replace with your own points of interest.

- **`amenities_weigths.csv`**  
  Contains standardized popularity and intensity scores for each amenity type (based on NAICS codes). These values are used to assign behavioral weights to each POI.


## 🚗 Quick Guide

This repository outlines the analytical logic rather than providing a ready-to-run Python script, since multiple tools can be used for each spatial step.

To replicate the analysis:

**1. Generate a Walkshed**
- Center point: Use the midpoint of each road segment.
- Distance type: *Eucledian distance* or *Network-based distance*. Tools such as HERE API can automate generating network-based walkshed moreeasily.
- Distance threshold: Defined based on your purpose - either a distance (e.g., 800 meters) or travel time (e.g., 10 minute walk)

**2. Collect POI Data**
Focus on amenities supporting daily needs, following the 15-minute city framework. This analysis includes 10 major amenity categories (Table #).

Obtain POI data with location, NAICS code, and operating hours from platforms such as SafeGraph, Google Places, or OpenStreetMap. Note: Not all platforms support these attributes but at least SafeGraph does.

**3. Compute Accessibility Scoresd**
Once you’ve identified all accessible POIs, compute a weighted composite score following the method below.

## 🔎 Methodology - Calculating a weighted composite score
Not all amenities contribute equally to daily life. Each POI’s importance is defined by three components:
  1. Popularity (**pop**): *How much an amenitiy attracts vistis*
  2. Intensity (**int**): *How long people dwell*
  3. Operating hour (**opr**):

**Popularity**
To calculate the standardized popularity score for each amenity type, we first calculated the average monthly visit counts for all points of interests for each category in the United States. In the figure 1, The blue bar represents the total # of POIs of a given category in the US and red point tells us the mean number of visits. So for example, each restaurant-related POI receives an average of 362 monthly visitors. Next, we standardize the average visit count using Min-Max standardization. See figure 2

**Intensity**
We first calculated the average dewll time which is mean of median dwell times for POIs across the US (Figure 3). Next using the similar logic like popularity, the standardized intensity score was retrieved (Figure 4)

**Operating Hours**
Lastly, we also account for operation hours per week for each unique POI. Because POI operating relatively longer ~~~, we defined a median operational time among POIs in the US. Out of the 9,823,558 POIs, 68% are found to record operational hours information, and the median operation time is 53 hours per week (Figure #). So we assign additional weight to amenity that operates more than 53 hours.
opr = 1.5 if operational time > 53; 1 otherwise

**Composite POI Weight**
Each POI's individual weight is calculated as:

m_j = opr_j × (1 + pop_j) × (1 + int_j)

opr = 1.5 if weekly operation hours exceed 53 hrs; otherwise, 1
pop = Min-Max standardized popularity score
int = Min-Max standardized intensity score
The multiplicative form assumes compounding effects of popularity, intensity, and availability.

**Composite Accessibility Score**
For each road segment i:

AmenityAccessibility_i = (∑_𝑗▒𝑚_𝑗 )/𝑁_𝑖 ×(1+ln⁡〖(𝑁+1)〗)÷ln⁡〖𝑙_𝑖 〗

i = road segment identifier
j = POI within the buffer of road segment I
l = length of road segment i
N = Number of POIs of road segment i
m = weight assigned to each POIj

This formulation balances amenity density with segment length, producing a dimensionless index representing accessibility richness per unit road length.






### References
If you use this model, please cite the following paper:
