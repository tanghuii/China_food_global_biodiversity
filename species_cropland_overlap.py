

import os
import numpy as np
import pandas as pd
from osgeo import gdal
import time

# ---------------------------------------------------------------------------
# File paths
# ---------------------------------------------------------------------------
species_folder = r"D:\Thesis2024\habitat_spe\BIRD_RC"  # Folder with species habitat rasters
cropland_path = r"D:\Thesis2024\cropland_expan\ANN\final_result\cropland_0326_onlynew_wgs84f.tif"  # Newly expanded cropland raster
species_table = r"D:\Thesis2024\habitat_table\bird_for_analysis_11.xlsx"  # Table listing the species IDs
output_excel = r"D:\Thesis2024\habitat_table\overlap\bird_overlap_2.xlsx"  # Output table
area_raster_path = r"D:\Thesis2024\chapter3\gridarea.tif"  # Per-pixel area raster (km2)
country_raster_path = r"D:\Thesis2024\chapter3\countries_f.tif"  # Country ID raster

# ---------------------------------------------------------------------------
# Read the species ID table
# ---------------------------------------------------------------------------
species_df = pd.read_excel(species_table)
species_list = species_df["id"].tolist()

# ---------------------------------------------------------------------------
# Load the raster layers
# ---------------------------------------------------------------------------
cropland_ds = gdal.Open(cropland_path)
cropland = cropland_ds.ReadAsArray().astype(np.uint8)

area_ds = gdal.Open(area_raster_path)
area_raster = area_ds.ReadAsArray().astype(np.float32)

country_ds = gdal.Open(country_raster_path)
country_raster = country_ds.ReadAsArray().astype(np.int32)

# Check that all rasters share the same extent
rows, cols = cropland.shape
if area_raster.shape != (rows, cols) or country_raster.shape != (rows, cols):
    raise ValueError("The area raster or country raster does not match the size of the cropland layer!")

# Build the array of country IDs
max_country_id = np.max(country_raster)
country_ids = np.arange(1, max_country_id + 1)
print(f"Country ID range: 1 to {max_country_id}")

# Container for the per-species results
results = []

# ---------------------------------------------------------------------------
# Build the output header
# ---------------------------------------------------------------------------
header = ["Species_ID", "Species_File", "Global_Total_Area", "Global_Overlap_Area","Global_Total_Pixel","Global_Overlap_Pixel"]

# One pair of columns per country: total area (TA) and overlap area (OA)
for country_id in country_ids:
    header.append(f"{country_id}_TA")
    header.append(f"{country_id}_OA")
    #header.append(f"{country_id}_TP")
    #header.append(f"{country_id}_OP")

# List the available species rasters
species_files = [f for f in os.listdir(species_folder) if f.endswith(".tif")]

# Keep only the rasters that are listed in the species table
matched_files = [f"{sp}.tif" for sp in species_list if f"{sp}.tif" in species_files]

print(f"Found {len(matched_files)} matching species rasters")

# ---------------------------------------------------------------------------
# Process every species raster
# ---------------------------------------------------------------------------
for i, species_file in enumerate(matched_files):
    start_time = time.time()  # Start of the timer

    print(f"Processing {i + 1}/{len(matched_files)}: {species_file}")

    # Read the species raster
    species_path = os.path.join(species_folder, species_file)
    species_ds = gdal.Open(species_path)

    # Make sure the raster matches the reference extent
    if species_ds.RasterXSize != cols or species_ds.RasterYSize != rows:
        print(f"Skipping {species_file}: raster size does not match the cropland layer")
        continue

    species = species_ds.ReadAsArray().astype(np.uint8)

    # Species ID taken from the file name
    species_id = species_file.replace('.tif', '')

    # Initialise the result record for this species with zeros
    species_result = {
        "Species_ID": species_id,
        "Species_File": species_file,
        "Global_Total_Area": 0,
        "Global_Overlap_Area": 0,
        "Global_Total_Pixel": 0,
        "Global_Overlap_Pixel": 0
    }

    # Pre-fill every country column with zero
    for country_id in country_ids:
        species_result[f"{country_id}_TA"] = 0
        species_result[f"{country_id}_OA"] = 0
        #species_result[f"{country_id}_TP"] = 0
        #species_result[f"{country_id}_OP"] = 0


    # Number of habitat pixels (value 1) and their total area
    total_pixels = np.sum(species == 1)
    total_area = np.sum((species == 1) * area_raster)

    # Pixels that overlap with newly expanded cropland
    overlap_pixels = np.sum((species == 1) & (cropland == 1))
    overlap_area = np.sum(((species == 1) & (cropland == 1)) * area_raster)

    # Global statistics
    species_result["Global_Total_Pixel"] = total_pixels
    species_result["Global_Overlap_Pixel"] = overlap_pixels
    species_result["Global_Total_Area"] = total_area
    species_result["Global_Overlap_Area"] = overlap_area

    intersecting_countries = np.unique(country_raster[species == 1])
    intersecting_countries = intersecting_countries[intersecting_countries > 0]  # Drop the 0 (no-data) value
    print(f"Species {species_id} intersects {len(intersecting_countries)} countries: {intersecting_countries}")

    # Country-level statistics
    for country_id in  intersecting_countries:
        country_mask = (country_raster == country_id)

        # Skip countries without data
        if np.sum(country_mask) == 0:
            species_result[f"{country_id}_TA"] = 0
            species_result[f"{country_id}_OA"] = 0
            continue

        # Habitat area and overlap area within the current country
        c_total_area = np.sum(((species == 1) & country_mask) * area_raster)  # square kilometres
        c_total_pixels = np.sum((species == 1)& country_mask)

        c_overlap_area = np.sum(((species == 1) & (cropland == 1) & country_mask) * area_raster)   # square kilometres
        c_overlap_pixels = np.sum((species == 1) & (cropland == 1) & country_mask)

        species_result[f"{country_id}_TA"] = c_total_area
        species_result[f"{country_id}_OA"] = c_overlap_area
        print(f"{country_id} done: total:{c_total_area}; overlap:{c_overlap_area}")

        #species_result[f"{country_id}_TP"] = c_total_pixels
        #species_result[f"{country_id}_OP"] = c_overlap_pixels
        # print(f"{country_id} done: totalpx:{c_total_area}; overlappx:{c_overlap_area}")
    # Store the statistics of the current species
    results.append(species_result)
    # Append the data to the Excel file
    #df = pd.DataFrame(results)
    # Check whether the file already exists and append if it does

    # Build the DataFrame
    df = pd.DataFrame(results)
    df.to_excel(output_excel, index=False)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Species {species_id} finished in {elapsed_time:.2f} s")

# ---------------------------------------------------------------------------
# Save the results to Excel
# ---------------------------------------------------------------------------
#df = pd.DataFrame(results)
#df.to_excel(output_excel, index=False)
print(f"Processing complete, results saved to {output_excel}")
