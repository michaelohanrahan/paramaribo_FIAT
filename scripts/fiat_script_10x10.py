# -*- coding: utf-8 -*-
"""
Panos Athanasiou
"""
import pandas as pd
from pathlib import Path
from shutil import copyfile
import xlrd
from xlutils.copy import copy
from osgeo import gdal, gdalconst
import numpy as np
import subprocess
from rasterstats import zonal_stats
import rioxarray
import matplotlib
import matplotlib.pyplot as plt
import xarray as xr
import geopandas as gpd


#%% Define paths

# results_set = 'BAU_current_climate_4rp_threshold_20'
# ["Reference_RoG_4rp_threshold_10_10x10","Reference_RoG_4rp_threshold_20_10x10"]
# results_set_to_run = ["BAU_20_07_4rp_threshold_10_10x10",
#                       "BAU_50_14_4rp_threshold_10_10x10",
#                       "BAU_current_climate_4rp_threshold_10_10x10",
#                       "ID_20_07_4rp_threshold_10_10x10",
#                       "ID_50_14_4rp_threshold_10_10x10"]

# results_set_to_run = ["BAU_20_07_4rp_threshold_20_10x10",
#                       "BAU_50_14_4rp_threshold_20_10x10",
#                       "BAU_current_climate_4rp_threshold_20_10x10",
#                       "ID_20_07_4rp_threshold_20_10x10",
#                       "ID_50_14_4rp_threshold_20_10x10"]

results_set_to_run = ["Reference_RoG_4rp_subtract_0p1_10x10",
                      "BAU_20_07_4rp_subtract_0p1_10x10",
                      "BAU_50_14_4rp_subtract_0p1_10x10",
                      "BAU_current_climate_subtract_0p1_10x10",
                      "ID_20_07_4rp_subtract_0p1_10x10",
                      "ID_50_14_4rp_subtract_0p1_10x10"]



def process_fiat_scenario(results_set):
    basemodel0 = Path( r"d:/d_paramaribo/fiat/03_fiat/2_FIAT_raster_10x10")
    hazard_maps = Path( r"d:/d_paramaribo/fiat/03_fiat/0_data/hazard_maps/"+results_set)
    output_path = Path( r"d:/d_paramaribo/fiat/03_fiat/4_Results").joinpath(hazard_maps.name)
    crs = 32621
        
    scenarios = []
    if results_set.startswith("Reference_RoG"):
        scenarios = ["current"]
    elif results_set.startswith("BAU_"):
        scenarios = ["future_bau"]
    elif results_set.startswith("ID_"):
        scenarios = ["future_intgrowth"]


    for scenario in scenarios:
        output_path2 = output_path.joinpath(scenario)
        if not output_path2.exists():
            output_path2.mkdir(parents=True)
            
    def reproject(src_filename, match_filename, dst_filename):
        # Source
        src = gdal.Open(src_filename, gdalconst.GA_ReadOnly)
        src_proj = src.GetProjection()
    
        # We want a section of source that matches this:
        match_ds = gdal.Open(match_filename, gdalconst.GA_ReadOnly)
        match_proj = match_ds.GetProjection()
        match_geotrans = match_ds.GetGeoTransform()
        wide = match_ds.RasterXSize
        high = match_ds.RasterYSize
    
        # Output / destination
        dst = gdal.GetDriverByName('GTiff').Create(dst_filename, wide, high, 1, gdalconst.GDT_Float32)
        dst.SetGeoTransform(match_geotrans)
        dst.SetProjection(match_proj)
        dst.GetRasterBand(1).SetNoDataValue(-9999)
        # Do the work
        gdal.ReprojectImage(src, dst, src_proj, match_proj, gdalconst.GRA_NearestNeighbour)
    
        del dst # Flush
    
        filehandle = gdal.Open(dst_filename)
        arr = filehandle.GetRasterBand(1).ReadAsArray()
        arr[np.isnan(arr)] = -9999
        del filehandle # Flush
    
        dst = gdal.GetDriverByName('GTiff').Create(dst_filename, wide, high, 1, gdalconst.GDT_Float32)
        dst.GetRasterBand(1).WriteArray(arr)
        dst.SetGeoTransform(match_geotrans)
        dst.SetProjection(match_proj)
    
    run_name = scenario
    
    fiat_root = Path(  r"d:/d_paramaribo/fiat/03_fiat/2_FIAT_raster_10x10")
    hazard_maps_path = Path( r"d:/d_paramaribo/fiat/03_fiat/0_data/hazard_maps/"+results_set)
    config_path = Path(r"d:/d_paramaribo/fiat/03_fiat/4_Results").joinpath(hazard_maps_path.name, run_name) / 'FIAT_config.xls'
    
    fiat_root = fiat_root.joinpath(scenario)
    
    output_path = Path(config_path).parent
    # Create output folder
    if not output_path.exists():
        output_path.mkdir(parents=True)
    
    # Location of FIAT configuration file
    base_config = fiat_root.joinpath("FIAT_configuration_base.xls")
    
    # Create folder if needed
    fold = hazard_maps_path
    fold_reproj = output_path.joinpath("Flood_maps")
    if not fold_reproj.exists():
        fold_reproj.mkdir(parents=True)
    # Reproject files to make sure they are aligning with the exposure rasters
    match_file = list(fiat_root.joinpath("exposure").glob("*.tif"))[0]
    for flood_map in list(fold.glob("*_rp_*.tif")):
        dst_filename = fold_reproj.joinpath(flood_map.name)
        reproject(str(flood_map), str(match_file), str(dst_filename))
    
    # Get paths of hazard maps based on folder
    hazard_maps = list(fold_reproj.glob("*_rp_*.tif"))
    
    # Get RPs of each hazard maps based on name convention
    rps = []
    for path in hazard_maps:
        name = path.stem.split("_")[2]
        if "p" in name:
            rp = float(name.split("p")[-1]) * 0.1
        else:
            rp = float(name)
        rps.append(rp)
        
    # Make dataframe
    df = pd.DataFrame({min(rps): hazard_maps, max(rps): rps}).sort_values(max(rps)).reset_index(drop=True)
    hazard_file = output_path.joinpath(f"flood_maps.csv")
    df.to_csv(hazard_file, index=False)
    
    # Copy config
    new_config = output_path.joinpath('FIAT_config.xls')
    
    # Change config
    config_file = xlrd.open_workbook(base_config)
    wb = copy(config_file)
    sheet = wb.get_sheet(0)
    sheet.write(1, 1, run_name)
    sheet.write(3, 1, str(hazard_file))
    sheet.write(2, 9, str(fiat_root.joinpath("vulnerability")))
    sheet.write(3, 9, str(fiat_root.joinpath("exposure")))
    sheet.write(4, 9, str(output_path))
    wb.save(new_config) # save the file
    
    # STEP 2 - Run FIAT-Raster
    config = output_path.joinpath('FIAT_config.xls')
    
    # FIAT_exe_path = Path(r"c:/Users/kingma/OneDrive - Stichting Deltares/Documents/Projects/Paramaribo/03_fiat/FIAT_International").joinpath("x64", "Delft-Fiat.exe")
    FIAT_exe_path = Path(r"D:/d_paramaribo/fiat/03_fiat/FIAT_International").joinpath("x64", "Delft-Fiat.exe")
    
    command = f"{FIAT_exe_path} {config}"
    print(command)
    
    result = subprocess.run(command, capture_output=True, text=True)
    print("stdout:", result.stdout)
    print("stderr:", result.stderr)
    
     
    run_check = Path('d:/d_paramaribo/fiat/03_fiat/4_Results/'+results_set+'/'+scenario+'/Risk.txt')
    output_path = Path(run_check.parent)
    resorts = str(basemodel0.joinpath(scenario).joinpath("resorts.geojson"))
    # resorts = str(Path(r'd:\Paramaribo\mdp_paramaribo\03_fiat\FIAT-Paramaribo_raster').joinpath("resorts.geojson"))
    crs = 32621
    
    # output_path = Path(run_check).parent
    
    # add crs to results
    map2array=[]
    
    for raster in output_path.glob("*_risk.tif"):
        with rioxarray.open_rasterio(raster) as tif:
            xar_map = tif.load()
            # add georeference to tif
            xar_map.rio.write_crs(crs, inplace=True)
            raster_new = str(raster.parent.joinpath(raster.stem)) + "_proj.tif"
            xar_map.rio.to_raster(raster_new)
        raster.unlink()
        xar_map = rioxarray.open_rasterio(raster_new)
        # print(xar_map)
        map2array.append(xar_map)
    
    # Calcualate total risk
    total_risk = map2array[0].copy(deep=True)
    
    total_risk[0, :, :] = 0
    total_risk[0, :, :] = sum([rast[0, :, :] for rast in map2array])
    
    total_risk_file = output_path.joinpath("total_risk_proj.tif")
    total_risk.rio.to_raster(total_risk_file)
    
    # Get resort results
    stats = zonal_stats(resorts, total_risk_file, stats="sum", geojson_out=True)
    # stats = zonal_stats(catchments, total_risk_file, stats="sum", geojson_out=True)
    
    df = pd.DataFrame({'Resort name': [val["properties"]["id"] for val in stats], 'Total risk': [val["properties"]["sum"] for val in stats]})
    df["Total risk"] = df["Total risk"].astype(float)
    df.to_csv(output_path.joinpath("total_risk_resorts.csv"), index=False)


for results_set in results_set_to_run:
    process_fiat_scenario(results_set)
