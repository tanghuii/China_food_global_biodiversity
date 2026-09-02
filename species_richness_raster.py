"""
Build a species richness raster by stacking individual species habitat rasters.

"""

import os
import glob
import numpy as np
from osgeo import gdal
import pandas as pd


# ---------------------------------------------------------------------------
# Input / output settings
# ---------------------------------------------------------------------------
out_name = "amp56"

folder_path = r"D:\Thesis2024\habitat_spe\AMP_RE2\AMP_RE2"  # Folder holding the species rasters
result = r"D:\Thesis2024\habitat_spe\richness"  # Output folder
excel_path = fr"D:\Thesis2024\habitat_table\bird_richness\amp_analysis_code_56.xlsx"  # Table listing the species IDs

# Read the "id" column from the Excel table
df = pd.read_excel(excel_path, dtype=str)  # Read the Excel file as strings
if "id" not in df.columns:
    raise ValueError("The Excel file has no 'id' column, please check the header!")

tif_ids = df["id"].dropna().astype(str).tolist()  # ID column without NaN values
tif_files = [os.path.join(folder_path, f"{tif_id}.tif") for tif_id in tif_ids]  # Build the full TIF paths

# Drop the files that do not exist
tif_files = [tif for tif in tif_files if os.path.exists(tif)]

# Make sure at least one valid TIF file remains
if not tif_files:
    raise FileNotFoundError("None of the TIF files listed in the Excel table exist, please check the path or file names!")

# Read the first raster to get the reference metadata
sample_raster = gdal.Open(tif_files[0])
cols = sample_raster.RasterXSize
rows = sample_raster.RasterYSize
geotransform = sample_raster.GetGeoTransform()
projection = sample_raster.GetProjection()
no_data_value = sample_raster.GetRasterBand(1).GetNoDataValue()  # NoData value

# Initialise the accumulation arrays
sum_array = np.zeros((rows, cols), dtype=np.float32)
count_array = np.zeros((rows, cols), dtype=np.float32)  # Counter array used to handle NoData pixels

# Read the rasters one by one and accumulate them
for i, tif in enumerate(tif_files):
    print(f"Processing {i+1}/{len(tif_files)}: {tif}")  # Show the current progress
    raster = gdal.Open(tif)
    band = raster.GetRasterBand(1)
    data = band.ReadAsArray()

    # Handle NoData values: skip the NoData pixels
    if no_data_value is not None:
        valid_mask = data != no_data_value  # Mask of the valid pixels
        sum_array[valid_mask] += data[valid_mask]
        count_array[valid_mask] += 1  # Count how often a pixel is valid
    else:
        sum_array += data
        count_array += 1

# Avoid division by zero when computing valid means
valid_pixels = count_array > 0
sum_array[~valid_pixels] = no_data_value  # Pixels that are NoData in every raster stay NoData

# Create the output TIF file
driver = gdal.GetDriverByName("GTiff")
out_raster = driver.Create(os.path.join(result, rf"{out_name}_richness_RC.tif"), cols, rows, 1, gdal.GDT_Float32)
out_raster.SetGeoTransform(geotransform)
out_raster.SetProjection(projection)
out_band = out_raster.GetRasterBand(1)
out_band.WriteArray(sum_array)

# Set the NoData value (if the source data has one)
if no_data_value is not None:
    out_band.SetNoDataValue(no_data_value)

out_raster.FlushCache()

print(f"Raster accumulation complete, result saved as {out_name}_richness_RC.tif")
