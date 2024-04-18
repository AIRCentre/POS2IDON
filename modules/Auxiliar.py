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
import requests
import zipfile

#################################################################################################
def input_checker():
    """
    This function checks inputs to confirm if they are correct.
    Input: User inputs based on User_Inputs.py
    Output: inputs_flag - Can be 0 if at least one input fails or 1 if all inputs pass. 
            log_list - Logging messages.
    """
    # Logging list
    log_list = []

    from configs.User_Inputs import search, service, service_options, roi, nrt_sensing_period, sensing_period
    from configs.User_Inputs import processing
    from configs.User_Inputs import download
    from configs.User_Inputs import atmospheric_correction
    from configs.User_Inputs import masking, masking_options
    from configs.User_Inputs import classification, classification_options
    from configs.User_Inputs import delete
    from configs.User_Inputs import s2l1c_products_folder, ac_products_folder, masked_products_folder, classification_products_folder
    
    inputs_flag = 1
    if isinstance(search, bool):
        inputs_flag = inputs_flag*1
    else:
        inputs_flag = inputs_flag*0
        log_list.append("'search' is not boolean.")

    if isinstance(service, str):
        inputs_flag = inputs_flag*1
    else:
        inputs_flag = inputs_flag*0
        log_list.append("'service' is not string.")

    if isinstance(service_options, dict):
        if len(service_options) == 1:
            if isinstance(service_options["filter"], str):
                inputs_flag = inputs_flag*1
            else:
                inputs_flag = inputs_flag*0
                log_list.append("'service_options' has incorrect values.")
        else:
            inputs_flag = inputs_flag*0
            log_list.append("'service_options' does not have dimension 1.")
    else:
        inputs_flag = inputs_flag*0
        log_list.append("'service_options' is not dictionary.")

    if isinstance(roi, dict):
        if len(roi) == 2:
            if (roi["type"]=="Polygon") and isinstance(roi["coordinates"], list):
                inputs_flag = inputs_flag*1
            else:
                inputs_flag = inputs_flag*0
                log_list.append("'roi' has incorrect values.")
        else:
            inputs_flag = inputs_flag*0
            log_list.append("'roi' does not have dimension 2.")
    else:
        inputs_flag = inputs_flag*0
        log_list.append("'roi' is not dictionary.")

    if isinstance(nrt_sensing_period, bool):
        inputs_flag = inputs_flag*1
    else:
        inputs_flag = inputs_flag*0
        log_list.append("'nrt_sensing_period' is not boolean.")

    if isinstance(sensing_period, tuple):
        if len(sensing_period) == 2:
            if isinstance(sensing_period[0], str) and isinstance(sensing_period[1], str):
                inputs_flag = inputs_flag*1
            else:
                inputs_flag = inputs_flag*0
                log_list.append("'sensing_period' values are not strings.")
        else:
            inputs_flag = inputs_flag*0
            log_list.append("'sensing_period' does not have dimension 2.")
    else:
        inputs_flag = inputs_flag*0
        log_list.append("'sensing_period' is not tuple.")

    if isinstance(processing, bool):
        inputs_flag = inputs_flag*1
    else:
        inputs_flag = inputs_flag*0
        log_list.append("'processing' is not boolean.")

    if isinstance(download, bool):
        inputs_flag = inputs_flag*1
    else:
        inputs_flag = inputs_flag*0
        log_list.append("'download' is not boolean.")

    if isinstance(atmospheric_correction, bool):
        inputs_flag = inputs_flag*1
    else:
        inputs_flag = inputs_flag*0
        log_list.append("'atmospheric_correction' is not boolean.")

    if isinstance(masking, bool):
        inputs_flag = inputs_flag*1
    else:
        inputs_flag = inputs_flag*0
        log_list.append("'masking' is not boolean.")

    if isinstance(masking_options, dict):
        if len(masking_options) == 9:
            if isinstance(masking_options["use_existing_ESAwc"], bool) and isinstance(masking_options["land_buffer"], int) and\
                isinstance(masking_options["threshold_values"], list) and isinstance(masking_options["dilation_values"], list) and\
                isinstance(masking_options["cloud_mask"], bool) and isinstance(masking_options["cloud_mask_threshold"], float) and\
                isinstance(masking_options["cloud_mask_average"], int) and isinstance(masking_options["cloud_mask_dilation"], int):
                inputs_flag = inputs_flag*1
            else:
                inputs_flag = inputs_flag*0
                log_list.append("'masking_options' has incorrect values.")
        else:
            inputs_flag = inputs_flag*0
            log_list.append("'masking_options' does not have dimension 9.")
    else:
        inputs_flag = inputs_flag*0
        log_list.append("'masking_options' is not dictionary.")

    if isinstance(classification, bool):
        inputs_flag = inputs_flag*1
    else:
        inputs_flag = inputs_flag*0
        log_list.append("'classification' is not boolean.")

    if isinstance(classification_options, dict):
        if len(classification_options) == 10:
            if isinstance(classification_options["split_and_mosaic"], bool) and isinstance(classification_options["classification_probabilities"], bool) and\
                isinstance(classification_options["ml_algorithm"], str) and isinstance(classification_options["model_path"], str) and\
                isinstance(classification_options["n_classes"], int) and isinstance(classification_options["features"], tuple) and\
                isinstance(classification_options["n_hchannels"], int) and isinstance(classification_options["features_mean"], list) and\
                isinstance(classification_options["features_std"], list):
                inputs_flag = inputs_flag*1
            else:
                inputs_flag = inputs_flag*0
                log_list.append("'classification_options' has incorrect values.")
        else:
            inputs_flag = inputs_flag*0
            log_list.append("'classification_options' does not have dimension 10.")
    else:
        inputs_flag = inputs_flag*0
        log_list.append("'classification_options' is not dictionary.")

    if isinstance(delete, dict):
        if len(delete) == 3:
            if isinstance(delete["original_products"], bool) and isinstance(delete["some_intermediate"], bool) and\
                isinstance(delete["all_intermediate"], bool):
                inputs_flag = inputs_flag*1
            else:
                inputs_flag = inputs_flag*0
                log_list.append("'delete' has incorrect values.")
        else:
            inputs_flag = inputs_flag*0
            log_list.append("'delete' does not have dimension 3.")
    else:
        inputs_flag = inputs_flag*0
        log_list.append("'delete' is not dictionary.")

    if isinstance(s2l1c_products_folder, str):
        inputs_flag = inputs_flag*1
    else:
        inputs_flag = inputs_flag*0
        log_list.append("'s2l1c_products_folder' is not string.")

    if isinstance(ac_products_folder, str):
        inputs_flag = inputs_flag*1
    else:
        inputs_flag = inputs_flag*0
        log_list.append("'ac_products_folder' is not string.")

    if isinstance(masked_products_folder, str):
        inputs_flag = inputs_flag*1
    else:
        inputs_flag = inputs_flag*0
        log_list.append("'masked_products_folder' is not string.")

    if isinstance(classification_products_folder, str):
        inputs_flag = inputs_flag*1
    else:
        inputs_flag = inputs_flag*0
        log_list.append("'classification_products_folder' is not string.")
    
    return inputs_flag, log_list

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
def git_clone_acolite_fels(save_dir):
    """
    This function clones  ACOLITE and FeLS from GitHub and extracts on a folder.
    Input: save_dir - Name (string) of the directory to save the modules.
    Output: Modules extracted on folder.
            log_list - Logging messages.
    """
    # Logging list
    log_list = []

    # ZIP urls
    acolite_zip_url = "https://github.com/acolite/acolite/archive/refs/tags/20231023.0.zip"
    acolite_name = "acolite-main"
    fels_zip_url = "https://github.com/EmanuelCastanho/fetchLandsatSentinelFromGoogleCloud/archive/master.zip"
    fels_name = "fetchLandsatSentinelFromGoogleCloud-master"

    acolite_path = os.path.join(save_dir, acolite_name)
    if not os.path.exists(acolite_path):
        log_list.append("Cloning ACOLITE from GitHub")
        try:
            # Download
            acolite_r = requests.get(acolite_zip_url)
            with open(acolite_path+".zip", 'wb') as acolite_f:
                acolite_f.write(acolite_r.content)
            
            # Unzip
            with zipfile.ZipFile(acolite_path+".zip") as acolite_zip:
                acolite_zip.extractall(save_dir)
            os.remove(acolite_path+".zip")

            # Rename from acolite-version to acolite-main
            acolite_freshly_path = glob.glob(os.path.join(save_dir, "acolite-*"))[0]
            os.rename(acolite_freshly_path, acolite_path)

        except Exception as e:
            log_list.append("Unable to clone ACOLITE - " + str(e))
    else:
        log_list.append("Cloning of ACOLITE from GitHub ignored") 

    # Download FeLS
    fels_path = os.path.join(save_dir, fels_name)
    if not os.path.exists(fels_path):
        log_list.append("Cloning FeLS from GitHub")
        try:
            fels_r = requests.get(fels_zip_url)
            with open(fels_path+".zip", 'wb') as fels_f:
                fels_f.write(fels_r.content)

            with zipfile.ZipFile(fels_path+".zip") as fels_zip:
                fels_zip.extractall(save_dir)
            os.remove(fels_path+".zip")
        except Exception as e:
            log_list.append("Unable to clone FeLS - " + str(e))
    else:
        log_list.append("Cloning of FeLS from GitHub ignored")

    return log_list

################################################################################################
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

    else:
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


        