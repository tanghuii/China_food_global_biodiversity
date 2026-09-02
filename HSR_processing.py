import pandas as pd
import os
import arcpy
from arcpy.sa import *
import time

arcpy.env.workspace = r"D:\Thesis2024\habitat_spe\BIRD1"  

table_path = (r"D:\Thesis2024\habitat_table\bird_excel\bird_analysis_code_11.xlsx")
df = pd.read_excel(table_path)

# DEM
demtif_path = r"D:\Thesis2024\landuse_recaculate\landuse2\globaldem_1km.tif"
dem_raster = arcpy.Raster(demtif_path)

# land use
fore_path = rf"D:\Thesis2024\landuse_recaculate\landuse2\forest.tif"
forest = Raster(fore_path)
grass_path = rf"D:\Thesis2024\landuse_recaculate\landuse2\grassland.tif"
grass = arcpy.Raster(grass_path)
shrub_path = rf"D:\Thesis2024\landuse_recaculate\landuse2\shrubland.tif"
shrub = Raster(shrub_path)
urban_path = rf"D:\Thesis2024\landuse_recaculate\landuse2\urban.tif"
urban = Raster(urban_path)
wetland_path = rf"D:\Thesis2024\landuse_recaculate\landuse2\wetland.tif"
wetland = Raster(wetland_path)
barren_path = rf"D:\Thesis2024\landuse_recaculate\landuse2\barren.tif"
barren = Raster(barren_path)
cropland_path = rf"D:\Thesis2024\landuse_recaculate\landuse2\cropland.tif"
cropland = Raster(cropland_path)
water_path = rf"D:\Thesis2024\landuse_recaculate\landuse2\water.tif"
water = Raster(water_path)

print(f"data inputed...")

land_use_files = {
    "forest": forest,
    "grassland": grass,
    "shrubland": shrub,
    "urban": urban,
    "wetland": wetland,
    "barren": barren,
    "cropland": cropland,
    "water": water
}

habitat_to_land_use = {
    "forest": [1, 14.3, 14.6, 16],  
    "grassland": [2, 4, 14.2, 14.4],  
    "shrubland": [3],  
    "urban": [14.5],  
    "wetland": [8, 5.3,5.4,5.7, 5.8, 5.12, 5.13, 5.16, 5.17],  
    "barren": [6, 8],  
    "cropland": [14.1],  
    "water": [9, 10, 11, 12, 13, 15, 5.1,5.2,5.5,5.6,5.9, 5.10, 5.11, 5.14, 5.15, 5.18]  
}


for index, row in df.iterrows():
    
    start_time = time.time()
    species_id = row['id']  
    elevation_upper = row['upperElevationLimit']  
    elevation_lower = row['lowerElevationLimit']  
    habitat_types = row['Processed']  

    
    if pd.isna(elevation_upper):
        elevation_upper = 8700  
    if pd.isna(elevation_lower):
        elevation_lower = -500  


    if elevation_upper == elevation_lower:
        elevation_upper += 1  

    species = Raster(r"D:\Thesis2024\ArcGIS_File\IUCN\BIRDTIF\{}.tif".format(species_id))


    reclass_dem = Con(dem_raster < elevation_lower, 0,
                      Con(dem_raster > elevation_upper, 0, 1))

    print(f"elevaion reclassifying {species_id}...")

    print(f"elevation done {species_id}...")

  
    habitat_types_list = [float(x) for x in str(habitat_types).split(';')]
    print(f"processing sepecies {species_id}...")

    habitat_final_raster = None

    processed_land_use = set()

    for habitat_type in habitat_types_list:
        if habitat_type == 17 or habitat_type == 18 or habitat_type == 7 or habitat_type == 19:
            continue
        print(f"  processing habitat {habitat_type}...")

        for land_use, habitat_range in habitat_to_land_use.items():
            if habitat_type in habitat_range:
                habitat_raster = land_use_files[land_use]

                print(f"{land_use} ({habitat_raster})")

                if land_use in processed_land_use:
                    print(f"    this type {land_use}has been processed before. Skip")
                    continue

                if habitat_final_raster is None:
                    habitat_final_raster = habitat_raster
                else:
                    habitat_final_raster += habitat_raster

                habitat_final_raster = Raster(habitat_final_raster)

                processed_land_use.add(land_use)
                print(f"{land_use} done")

    if set(habitat_types_list) == {18}:  
        output = species * reclass_dem  # don't multiple habitat_final_raster
    elif set(habitat_types_list) == {7}:
        output = species * reclass_dem  # don't multiple habitat_final_raster
    elif set(habitat_types_list) == {7,18}:
        output = species * reclass_dem  # multiple habitat_final_raster
    elif set(habitat_types_list) == {19}:
        output = species * reclass_dem  # multiple habitat_final_raster
    elif set(habitat_types_list) == {17}:
        output = species * reclass_dem  # multiple habitat_final_raster
    else:
        output = species * reclass_dem * habitat_final_raster  


    output.save(r"D:\Thesis2024\habitat_spe\BIRD_RC\{}.tif".format(species_id))

    print(f"{species_id}.tif done...")
    end_time = time.time()

    elapsed_time = end_time - start_time
    print(f"species {species_id} ; time lasting: {elapsed_time:.2f} 秒")

print("Done. All tasks done!")
