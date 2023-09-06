#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
Auxiliar Functions.

@author: AIR Centre
"""

### Import Libraries ############################################################################
import os
import shutil
import glob
from datetime import datetime, timedelta
from osgeo import gdal
import pandas as pd

############################################################################################
def check_folder(folder_name):
    """
    This function checks if a folder exists and if it is empty or not.
    Input:  folder_name - Name of the folder to be checked.
    Output: status - "00" folder does not exist;
                     "10" folder exists but it is empty;
                     "11" folder exists and has data.
    """
    if os.path.exists(folder_name):
        if os.listdir(folder_name):
            status = "11"
        else:
            status = "10"
    else:
        status = "00" 

    return status

#################################################################################################
def CreateBrandNewFolder(FolderName):
    """
    This function creates a folder if doesnt exist. If the folder exists, the function 
    deletes it and creates a new one.
    Input:  FolderName - Name of the folder to be created.
    Output: Brand new folder.
    """
    if not os.path.exists(FolderName):
        os.mkdir(FolderName)
    else:
        shutil.rmtree(FolderName)
        os.mkdir(FolderName)

#################################################################################################
def delete_folder(folder_path):
    """
    This function deletes a folder.
    Input: folder_path - Path to the folder that will be deleted.
    Output: Deletes a folder.
    """
    # Check if folder exists
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)

#################################################################################################
def delete_file(file_path):
    """
    This function deletes a file.
    Input: file_path - Path to the file that will be deleted.
    Output: Deletes a file.
    """
    # Check if file exists
    if os.path.exists(file_path):
        os.remove(file_path)

#################################################################################################
def NearRealTimeSensingDate():
    """
    This function, together with a crontab, is useful in a server to get the last sensing peiod.
    Input:  -
    Output: SensingPeriod - Sensing Period as tuple of Yesterday's and Today's dates.
    """
    Today = datetime.today()
    Yesterday = Today - timedelta(days=1)
    TodayFormat = Today.strftime("%Y%m%d")
    YesterdayFormat = Yesterday.strftime("%Y%m%d")
    SensingPeriod = (YesterdayFormat,TodayFormat)

    return SensingPeriod

#################################################################################################
def GenerateTifPaths(FolderPath, StringList=["B01","B02","B03","B04","B05","B06","B07","B08","B8A","B11","B12"]):
    """
    This function combines string elements of a list with folder path adding .tif extension. This can prevent confusion between B08 and B8A during sort: 
    sorted(List, key=lambda x: int("".join([i for i in x if i.isdigit()]))) works only if B8 and not B08.
    Input:  FolderPath - Path to folder that will be combined with elements of list.
            StringList - List of strings that will be combined with folder path and .tif extension.
    Output: TifPathsList - List of paths to the TIF files.
    """
    TifPathsList = []
    for p in StringList:
        TifPathsList.append(os.path.join(FolderPath, p+".tif"))
    
    return TifPathsList

#################################################################################################
def delete_intermediate(ac_product, masked_product, classification_product, mode):
    """
    This function deletes intermediate files and folders according to product name and mode.
    Input:  ac_product - Atmospheric correction product folder.
            masked_product - Masked product folder.
            classification_product - Classification product folder.
            mode - "all" or "some".
    Output: Deletes files and folders.
    """
    if mode == "all":
        # -> Atmospheric Correction
        # Surface_Reflectance_Bands
        surface_reflectance_bands = os.path.join(ac_product, "Surface_Reflectance_Bands")
        delete_folder(surface_reflectance_bands)
        # Top_Atmosphere_Bands
        top_atmosphere_bands = os.path.join(ac_product, "Top_Atmosphere_Bands")
        delete_folder(top_atmosphere_bands)
        # AC Stack
        ac_stack = glob.glob(os.path.join(ac_product, "*stack.tif"))[0]
        delete_file(ac_stack)
        
        # -> Masking
        # Masks 
        masks = os.path.join(masked_product, "Masks")
        delete_folder(masks)
        # Masked Patches
        masked_patches = os.path.join(masked_product, "Patches")
        delete_folder(masked_patches)
        # Masked Stack
        masked_stack = glob.glob(os.path.join(masked_product, "*stack.tif"))[0]
        delete_file(masked_stack)

        # -> Classification
        # sc_maps
        sc_maps = os.path.join(classification_product, "sc_maps")
        # Mosaics
        sc_mosaics = os.path.join(sc_maps, "Mosaics")
        delete_folder(sc_mosaics)
        # Single TIFs
        sc_single_tifs = glob.glob(os.path.join(sc_maps, "*patch*scmap.tif"))
        for single_tif in sc_single_tifs:
            delete_file(single_tif)

        # proba_maps
        proba_maps = os.path.join(classification_product, "proba_maps")
        # Mosaics
        proba_mosaics = os.path.join(proba_maps, "Mosaics")
        delete_folder(proba_mosaics)
        # Single TIFs
        proba_single_tifs = glob.glob(os.path.join(proba_maps, "*patch*probamap.tif"))
        for single_tif in proba_single_tifs:
            delete_file(single_tif)

    elif mode == "some":
        # -> Atmospheric Correction
        # Surface_Reflectance_Bands
        surface_reflectance_bands = os.path.join(ac_product, "Surface_Reflectance_Bands")
        delete_folder(surface_reflectance_bands)
        # Top_Atmosphere_Bands
        top_atmosphere_bands = os.path.join(ac_product, "Top_Atmosphere_Bands")
        delete_folder(top_atmosphere_bands)
        
        # -> Masking
        # Masked Patches
        masked_patches = os.path.join(masked_product, "Patches")
        delete_folder(masked_patches)

        # -> Classification
        # sc_maps
        sc_maps = os.path.join(classification_product, "sc_maps")
        # Mosaics
        sc_mosaics = os.path.join(sc_maps, "Mosaics")
        delete_folder(sc_mosaics)
        # Single TIFs
        sc_single_tifs = glob.glob(os.path.join(sc_maps, "*patch*scmap.tif"))
        for single_tif in sc_single_tifs:
            delete_file(single_tif)

        # proba_maps
        proba_maps = os.path.join(classification_product, "proba_maps")
        # Mosaics
        proba_mosaics = os.path.join(proba_maps, "Mosaics")
        delete_folder(proba_mosaics)
        # Single TIFs
        proba_single_tifs = glob.glob(os.path.join(proba_maps, "*patch*probamap.tif"))
        for single_tif in proba_single_tifs:
            delete_file(single_tif)

    else:
        print("Mode not available.")

#################################################################################################
def filter_safe_products(urls_list, filter):
    """
    This function filters SAFE products URLs.
    Inputs: urls_list - List with all products URLs. 
            filter - Filter specific combinations in the products URLs. String.
    Outputs: urls_list_filtered - List of products URLs to consider.
             urls_list_ignored - List of products URLs to ignore.
    """
    urls_list_filtered = []
    urls_list_ignored = []
    if filter != "":
        for i, url in enumerate(urls_list):
            safe_file_name = url.split('/')[-1]
            if filter in safe_file_name:
                urls_list_filtered.append(url)
            else:
                urls_list_ignored.append(url)
    else:
        urls_list_filtered = urls_list.copy()

    return urls_list_filtered, urls_list_ignored

#################################################################################################
def raster_to_feather(input_path):
    """
    This function converts a GeoTIF raster to a feather file with X, Y, Value.
    Inputs: input_path - Path to the GeoTIF file as string.
    Output: Feather file with same name as input file.
    """
    folder_path = os.path.dirname(input_path)
    input_name = os.path.basename(input_path)[:-4]

    # Convert GeoTIFF to XYZ format
    raster = gdal.Open(input_path)
    xyz_path = os.path.join(folder_path, input_name+".xyz")
    xyz = gdal.Translate(xyz_path, raster)
    raster = None
    xyz = None

    # Convert XYZ to Feather and delete it
    xyz_df = pd.read_csv(xyz_path, sep=" ", header=None)
    xyz_df.columns = ["X", "Y", "Value"]
    feather_path = os.path.join(folder_path, input_name+".feather")
    xyz_df.to_feather(feather_path)
    os.remove(xyz_path)


        