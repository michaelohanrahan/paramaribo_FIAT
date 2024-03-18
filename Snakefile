
data_folder = "WINTI_TEST"

rule all:
    input:
        expand("../data/2-interim/" + data_folder + "/tifffiles/{run}.tif", run=["Flood_rp_0p1", "Flood_rp_1", "Flood_rp_10", "Flood_rp_100"])

rule prep_folders:
    params:
        data_folder = data_folder
    output:
        nc_file = "../data/2-interim/" + data_folder + "/foufiles/{run}_fou.nc"
    script:
        "scripts/00_prep_folders.py"

rule unstruct_2_raster:
    input:
        nc_file = rules.prep_folders.output.nc_file
    params:
        data_folder = data_folder,
        fn_dem = 'bedlevel_10x10.tif',
        res_2d = 10,
        max_search_1d = 250
    output:
        "../data/2-interim/" + data_folder + "/tifffiles/{run}.tif"
    script:
        "scripts/01_unstr2raster.py"