# -*- coding: utf-8 -*-
"""
Created on Fri Feb 23 12:02:12 2024

@author: kingma
"""


from optparse import OptionParser
import xarray as xr
import matplotlib.pyplot as plt
import rasterio
import rasterio.fill
import os
import numpy as np
from scipy.signal import convolve2d
from pathlib import Path

#%% Change the pilot name and the names of the .nc files that you want to convert to .tiff
runfolder = 'test'

runs = [
        "Flood_T0p1_fou.nc", 
        "Flood_T1_fou.nc",
        "Flood_T10_fou.nc",
        "Flood_T100_fou.nc"
        ]

#%%
fn_path = rf"c:\paramaribo\fiat\floodmap_postprocessing\{runfolder}\foufiles"
dst_path = rf"c:\paramaribo\fiat\floodmap_postprocessing\{runfolder}\tiffiles"
os.makedirs(dst_path) if not os.path.exists(dst_path) else None
fn_dem = r"c:/paramaribo/fiat/bedlevel_100x100.tif"

def clip_coords(ds, xs, ys):
    xmin, ymin, xmax, ymax = ds.bounds
    idx = np.all(np.array([xs > xmin, xs < xmax, ys > ymin, ys < ymax]), axis=0)
    return idx

def round_up_to_odd(f):
    f = int(np.ceil(f))
    return f + 1 if f % 2 == 0 else f


# Note that in some versions of D-HYDRO, the mesh2d output starts with a capital 
# In the case of the error "No variable named 'mesh2d_face_x', change the following: 
    #    var_x2d="Mesh2d_face_x",
    #    var_y2d="Mesh2d_face_y",
    #    var_h2d="Mesh2d_fourier002_max",
    #    var_d2d="Mesh2d_fourier002_max_depth",
def read_1d2d(
    fn,
    var_x2d="mesh2d_face_x",
    var_y2d="mesh2d_face_y",
    var_x1d="mesh1d_node_x",
    var_y1d="mesh1d_node_y",
    var_z1d="mesh1d_flowelem_bl",
    var_h2d="mesh2d_fourier002_max",
    var_d2d="mesh2d_fourier002_max_depth",
    var_h1d="mesh1d_fourier002_max",
    var_d1d="mesh1d_fourier002_max_depth",
):
    ds = xr.open_dataset(fn, engine='netcdf4')
    results = {}
    results["x2d"] = ds[var_x2d][:].values
    results["y2d"] = ds[var_y2d][:].values
    results["h2d"] = ds[var_h2d][:].values
    results["d2d"] = ds[var_d2d][:].values
    results["x1d"] = ds[var_x1d][:].values
    results["y1d"] = ds[var_y1d][:].values
    results["h1d"] = ds[var_h1d][:].values
    results["d1d"] = ds[var_d1d][:].values
    results["z1d"] = ds[var_z1d][:].values
    return results


def flood_map(
    ds,
    x1d,
    y1d,
    h1d,
    d1d,
    z1d,
    x2d,
    y2d,
    h2d,
    d2d,
    resolution_2d,
    use_dem_1d=False,
    use_dem_2d=True,
    depth_thres=0.00,
    max_search_distance_1d=100.0,
    smoothing_iter=1,
):
    dem_resolution = ds.transform[0]
    res_diff = round_up_to_odd(resolution_2d / dem_resolution)
    conv_arr = np.ones((res_diff, res_diff))

    # estimate the search distance (radius) for 2D. The search distance in meters is half the size of a grid cell in y, as well as x direction
    radius = resolution_2d / 2
    max_search_distance_2d = np.ceil(
        np.sqrt(radius ** 2 + radius ** 2) / dem_resolution
    )

    print("Clipping data coordinates")
    # only store those coordinates that lie within the terrain model provided
    idx = clip_coords(ds, x1d, y1d)
    x1d, y1d, h1d, z1d, d1d = x1d[idx], y1d[idx], h1d[idx], z1d[idx], d1d[idx]
    idx = clip_coords(ds, x2d, y2d)
    x2d, y2d, d2d, h2d = x2d[idx], y2d[idx], d2d[idx], h2d[idx]

    # make a new raster with the same shape and properties
    elev = ds.read(1)
    # elev_grid = convolve2d(elev, conv_arr/conv_arr.sum())
    dst = np.zeros(elev.shape, dtype=np.float32)
    dst2 = np.zeros(elev.shape, dtype=np.float32)
    mask = np.zeros(elev.shape)
    rows1d, cols1d = rasterio.transform.rowcol(ds.transform, x1d, y1d)
    rows2d, cols2d = rasterio.transform.rowcol(ds.transform, x2d, y2d)


    print("preparing mask by estimating cells that are covered by 2D resolution")
    mask[rows2d, cols2d] = 1
    mask = np.minimum(convolve2d(mask, conv_arr, mode="same"), 1)

    if use_dem_1d:
        print("Estimating 1D water level by adding terrain at 1D cells to depth")
        dst[rows1d, cols1d] = d1d + elev[rows1d, cols1d]
    else:
        print(
            "Estimating 1D water level by adding water depth to bed level at 1D cells"
        )
        dst[rows1d, cols1d] = d1d + z1d
    # dst[rows1d, cols1d] = h1d

    print("Estimating flooding from 1D cells")
    dst = rasterio.fill.fillnodata(
        dst, mask=dst, max_search_distance=max_search_distance_1d
    )

    # remove areas that are within 2D domain
    dst[mask > 0] = 0.0

    # first exclude very thin layers of water
    idx = d2d < depth_thres
    # make largely negative so that these areas are definitely not inundating
    d2d[idx] = -2.0
    h2d[idx] = -2.0
    rows2d, cols2d = rasterio.transform.rowcol(ds.transform, x2d, y2d)

    # # fill in known points
    if use_dem_2d:
        dst2[rows2d, cols2d] = d2d + elev[rows2d, cols2d]
    else:
        dst2[rows2d, cols2d] = h2d

    print("Estimating flooding from 2D cells")
    dst2 = rasterio.fill.fillnodata(
        dst2, mask=dst2, max_search_distance=max_search_distance_2d
    )
    dst2[mask == 0] = 0.0
    dst2[dst2 == 0] = dst[dst2 == 0]

    # smooth to prevent jumps in water level
    for n in range(smoothing_iter):
        dst2 = convolve2d(dst2, conv_arr / conv_arr.sum(), mode="same")

    flood = np.maximum(dst2 - elev, 0)
    flood[flood < 0.000] = 0.0
    # remove ocean values
    # flood[elev <= 0.0] = 0.0
    return np.float32(flood)


# fn_fm = snakemake.input.fou_file
# fn_dem = snakemake.params.dem
# output = snakemake.output.hazard_file
# dst_path = Path(snakemake.params.dest_dir)
# res_2d = snakemake.params.res
# max_search_1d = snakemake.params.res




# fn_fm = os.path.join(dst_path, r"d:\projects\2023\Paramaribo\03_fiat\floodmap_postprocessing\pilot_fou\DFLOWFM_fou.nc")


# # input
res_2d = 100
use_dem_1d = False 
use_dem_2d = True  # when set to True, water levels in 2D domain are estimate through the depth + the centre coordinate dem value, otherwise the water pressure level is used
max_search_1d = 100  # amount of dem resolution grid cells around 1D nodes to fill from 1D elements. Make sure it is large enough
smoothing_iter = 1


var_list = ["x2d", "y2d", "h2d", "d2d", "x1d", "y1d", "h1d", "d1d", "z1d"]
# create dict with empty arrays
results_fm = {var: np.array([]) for var in var_list}
# read all fm files
for run in runs: 
    fn_fm = os.path.join(fn_path,run)
    fns = fn_fm.split(',')
    
    name_file = run.split('.')[0]
    output = os.path.join(dst_path, name_file+".tif")
    mask_tif = os.path.join(dst_path, "mask.tif")

    for fn in fns:
        if len(fn) > 0:
            results = read_1d2d(fn)
            # concatenate all data from all files together in one
            for var in var_list:
                results_fm[var] = np.hstack([results_fm[var], results[var]])
    
    with rasterio.open(fn_dem, "r") as ds:
        flood = flood_map(
            ds,
            resolution_2d=res_2d,
            use_dem_1d=use_dem_1d,
            use_dem_2d=use_dem_2d,
            max_search_distance_1d=max_search_1d,
            **results_fm, )
        
    with rasterio.open(output,
        "w",
        driver="GTiff",
        height=flood.shape[0],
        width=flood.shape[1],
        count=1,
        dtype=flood.dtype,
        crs=ds.crs,
        transform=ds.transform,
        nodata=0.0,
        compress='deflate'
    ) as dw:
        dw.write(flood, 1)

# dst_path = r"c:\Work\05_Projects\05_07_HYD\Paramaribo\paramaribo_snakemake\model_result\reference"    
# fn = os.path.join(dst_path, r"c:\Work\05_Projects\05_07_HYD\Paramaribo\paramaribo_snakemake\model_result\reference\hazard\tide_spring_T0p1\tide_spring_T0p1_fou.nc")

# ds = xr.open_dataset(fn, engine='netcdf4')