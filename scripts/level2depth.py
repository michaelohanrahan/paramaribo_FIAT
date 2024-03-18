import os
import rasterio
import numpy as np
from pathlib import Path


# Define the list of input folders
threshold = 0.20
input_folder = Path(r"c:\paramaribo\fiat\floodmap_postprocessing\runx\tiffiles\floodmap_subtract_20cm\waterlevel_10x10")
output_folder =  r"c:\paramaribo\fiat\floodmap_postprocessing\runx\tiffiles\floodmap_subtract_20cm\waterdepth_10x10"
os.makedirs(output_folder, exist_ok=True)
bedlevel_file = r"c:\paramaribo\fiat\bedlevel_10x10.tif"

# Iterate over the input folders
# for input_folder in input_folders:
#     # Create the output folder if it doesn't exist
#     output_folder = os.path.join(input_folder, '..', 'waterdepth_10x10')
#     os.makedirs(output_folder, exist_ok=True)

#     # List of return periods and corresponding file names
#     return_periods = [100, 10, 1, 0.1]
#     return_period_files = ["Flood_rp_100_wl.tif", "Flood_rp_10_wl.tif", "Flood_rp_1_wl.tif", "Flood_rp_0p1_wl.tif"]

#     # Iterate over the return periods and create water level files
#     for rp, rp_file in zip(return_periods, return_period_files):
        
for rp_file in list(input_folder.glob("*.tif")):
    rp_file_path = os.path.join(input_folder, rp_file)
    # rp_file_path = os.path.join(input_folder, rp_file)

    with rasterio.open(rp_file_path) as src:
        rp_data = src.read(1)  # Assuming the water depth is stored in the first band

        # Replace -9999 values with 0
        # rp_data = np.where(rp_data == -9999, 0, rp_data)

    # Read the bedlevel data
    with rasterio.open(bedlevel_file) as src:
        bedlevel_data = src.read(1)  # Assuming the bedlevel is stored in the first band

    bedlevel_data = np.where(bedlevel_data == -9999, 0, bedlevel_data)
    # Calculate the water level by subtracting the bedlevel from the water depth
    water_level_data = rp_data - bedlevel_data
    water_level_data = np.where(water_level_data < threshold, -9999, water_level_data)

    # Define the output file name with the "_wl" suffix
    # output_file_name = os.path.splitext(rp_file)[0][:-3] + ".tif"
    output_file_name = rp_file.name[:-7] + "_wd.tif"

    output_file_path = os.path.join(output_folder, output_file_name)

    # Save the water level data as a new TIFF file
    with rasterio.open(output_file_path, 'w', driver='GTiff', height=water_level_data.shape[0],
                       width=water_level_data.shape[1], count=1, dtype=str(water_level_data.dtype),
                       crs=src.crs, transform=src.transform,nodata=-9999) as dst:
        dst.write(water_level_data, 1)

    print(f"Water level TIFF file saved as {output_file_path}")
