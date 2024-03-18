import pandas as pd
from pathlib import Path
from shutil import copyfile
from osgeo import gdal, gdalconst
import numpy as np
import os 

#%%
runfolder = 'test'

#%%
current = Path(r"c:/paramaribo/fiat/floodmap_postprocessing/"+runfolder+"/tiffiles")
subtract = Path(r"c:/paramaribo/fiat/floodmap_postprocessing/"+runfolder+"/tiffiles/floodmap_subtract_20cm")
os.makedirs(subtract, exist_ok=True)

threshold = 0.20
sub = 'True'  #When we want to subtract 20 cm of each cell (verhoogde vloer)
thr = 'False' #When we want to set all the values below 20 cm to 0 (drempel)

for flood_map in list(current.glob("*.tif")):
    src = gdal.Open(str(flood_map), gdalconst.GA_ReadOnly)
    match_proj = src.GetProjection()
    match_geotrans = src.GetGeoTransform()
    wide = src.RasterXSize
    high = src.RasterYSize

    dst_filename = subtract.joinpath(flood_map.name)
    dst = gdal.GetDriverByName('GTiff').Create(str(dst_filename), wide, high, 1, gdalconst.GDT_Float32)
    dst.SetGeoTransform(match_geotrans)
    dst.SetProjection(match_proj)
    dst.GetRasterBand(1).SetNoDataValue(-9999)

    arr = src.GetRasterBand(1).ReadAsArray()
    
    if sub == 'True':
        arr2 = arr - threshold  # alleen een drempel
        arr2[arr2<0] = np.nan
        arr[np.isnan(arr2)] = -9999
        dst.GetRasterBand(1).WriteArray(arr2)
    if thr == 'True' : 
        arr2 = arr   # alleen een drempel
        arr2[arr2<threshold] = np.nan
        arr[np.isnan(arr2)] = -9999
        dst.GetRasterBand(1).WriteArray(arr2)

    del dst

    
    
