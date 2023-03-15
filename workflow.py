#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
Main POS2IDON script.

Atlantic International Research Centre (AIR Centre - EO LAB), Terceira, Azores, Portugal.

@author: AIR Centre
"""
### FULL PRÉ-START #########################################################################
print("\n")
print("|----------------------------------------------------------------------------|")
print("| WELCOME TO POS2IDON - Pipeline for ocean feature detection with Sentinel 2 |")
print("|----------------------------------------------------------------------------|")
print("\n")

# Init script outputs list to save as log file
log_list = ["\nWELCOME TO POS2IDON - Pipeline for ocean feature detection with Sentinel 2 \n"]

# Pré-start functions
try:
    print("Importing Pré-start functions...")
    from modules.PreStart import CloneModulesFromGitHub, ScriptOutput2List, ScriptOutputs2LogFile, input_checker
    print("Done.\n")
    pre_start_functions_flag = 1
except Exception as e:
    print(str(e) + '\n')
    pre_start_functions_flag = 0

# Clone important modules from GitHub (FeLS and ACOLITE)
try:
    CloneModulesFromGitHub("configs")
    clone_flag = 1
except Exception as e:
    print(str(e) + '\n')
    clone_flag = 0

# Import libraries
try:
    print("Importing Libraries...")
    import os
    from dotenv import load_dotenv
    import glob
    import time

    # Start time of POS2IDON
    POS2IDON_time0 = time.time()

    print("Done.\n")
    libraries_flag = 1
except Exception as e:
    print(str(e) + "\n")
    libraries_flag = 0

# Import defined modules
try:
    print("Importing Defined Modules...")
    from modules.Auxiliar import * 
    from modules.S2L1CProcessing import *
    from modules.S2L2Processing import *
    from modules.Masking import *
    from modules.SpectralIndices import *
    from modules.Tiling import *
    from modules.Classification import *
    print("Done.\n")
    modules_flag = 1
except Exception as e:
    print(str(e) + "\n")
    modules_flag = 0

# Import user inputs
try:
    inputs_flag = 1
    print("Importing User Inputs...")
    from configs.User_Inputs import *
    print("Done.")
    # Input checker
    print("Checking User Inputs...")
    inputs_flag = input_checker()
    print("Done.\n")
except Exception as e:
    print(str(e) + "\n")
    inputs_flag = 0

# Import credentials
try:
    print("Importing Credentials...")
    # Path of .env file
    basepath = os.getcwd()
    env_path = os.path.join(basepath,"configs/Environments/.env")
    if os.path.exists(env_path):
        # Environment variables
        evariables = ("COAHuser", "COAHpassword", "TSuser", "TSpassword", "EDuser", "EDpassword")
        load_dotenv(env_path)
        credentials_flag = 1
    else:
        print("Check credentials .env file.")
        credentials_flag = 0
    print("Done.\n")
except Exception as e:
    print(str(e) + "\n")
    credentials_flag = 0

pre_start_flag = pre_start_functions_flag * clone_flag * \
    libraries_flag * modules_flag * inputs_flag * credentials_flag
############################################################################################ 
if pre_start_flag == 1:

    # Start main processing time
    mp_time0 = time.time()

    # SEARCH PRODUCTS ######################################################################
    ScriptOutput2List("SEARCH PRODUCTS", log_list)
    if search == True:
        # Create folder to store products
        CreateBrandNewFolder(s2l1c_products_folder)

        # Sensing Period definition
        if nrt_sensing_period == True:
            ScriptOutput2List("Using Yesterday date as Start Date...", log_list)
            sensing_period = NearRealTimeSensingDate()

        # Search products using GC or COAH
        try:
            if service == "COAH":
                log_list_append = CollectDownloadLinkofS2L1Cproducts_COAH(os.getenv(evariables[0]), os.getenv(evariables[1]), roi, sensing_period, s2l1c_products_folder)  
            elif service == "GC":
                log_list_append = CollectDownloadLinkofS2L1Cproducts_GC(roi, sensing_period, "configs", s2l1c_products_folder) 
            else:
                ScriptOutput2List("Copernicus Ecosystem", log_list)   
        except Exception as e:
            ScriptOutput2List(str(e) + "\n", log_list)
    else:
        ScriptOutput2List("Search of products ignored.\n", log_list)

    # STREAM PROCESSING ####################################################################
    ScriptOutput2List("STREAM PROCESSING", log_list)
    urls_file = os.path.join(s2l1c_products_folder, "S2L1CProducts_URLs.txt")
    if (stream_processing == True) and os.path.isfile(urls_file):
        # Read S2L1CProducts_URLs.txt file        
        urls_list = open(urls_file).read().splitlines()
        if len(urls_list) == 0:
            ScriptOutput2List("List of product urls is empty.\n", log_list)
        else:
            # Create outputs folders
            if atmospheric_correction == True:
                CreateBrandNewFolder(ac_products_folder)
            if masking == True:
                CreateBrandNewFolder(masked_products_folder)
            if masking_options["use_existing_ESAwc"] == False:
                esa_wc_folder = "2-1_ESA_Worldcover"
                CreateBrandNewFolder(esa_wc_folder)
            else:
                esa_wc_folder = "2-1_ESA_Worldcover"
            if classification == True:
                CreateBrandNewFolder(classification_products_folder)

            # Create lists of excluded products names to print in the log file
            excluded_products_old_format = []
            excluded_products_no_data_sensing_time = []
            excluded_products_corrupted = []
            coah_lta_products = []

            # Start loop on urls list
            ScriptOutput2List("", log_list)
            for i, url in enumerate(urls_list):
                # Get SAFE file name from url link
                safe_file_name = url.split('/')[-1]
                safe_file_path = os.path.join(s2l1c_products_folder, safe_file_name)
                ScriptOutput2List("(" + str(i+1) +  "/" + str(len(urls_list)) + "): " + safe_file_name + "\n", log_list)
                
                try:        
                    # -> Download
                    if download == True:
                        # Delete old product that might be corrupted
                        if os.path.exists(safe_file_path):
                            shutil.rmtree(safe_file_path)
                        if service == "COAH":
                            log_list_append = DownloadTile_from_URL_COAH(os.getenv(evariables[0]), os.getenv(evariables[1]), url, s2l1c_products_folder, LTAattempt=download_options["lta_attempts"])
                            # Check if file is not retrievable from the COAH Long Term Archive
                            if not os.path.exists(safe_file_path):
                                coah_lta_products.append(safe_file_name) 
                                ScriptOutput2List("Download of "+safe_file_name+" from Long Term Archive not available.\n", log_list)  
                        elif service == "GC":
                            log_list_append = DownloadTile_from_URL_GC(url, s2l1c_products_folder)
                            # Check if OPER file was excluded
                            if not os.path.exists(safe_file_path):
                                excluded_products_old_format.append(safe_file_name)
                                ScriptOutput2List("The scene is in the redundant OPER old-format (before Nov 2016).Product excluded.\n", log_list)
                        else:
                            ScriptOutput2List("Copernicus Ecosystem", log_list)
                    else:
                        ScriptOutput2List("Download of product ignored.\n", log_list)
                except Exception as e:
                    ScriptOutput2List("An error occured during download.\n", log_list)

                try:
                    # URL list is the reference for product selection used during processing
                    product_in_urls_list = glob.glob(safe_file_path)
                    if len(product_in_urls_list)==1:
                        product_short_name = Extract_ACOLITE_name_from_SAFE(product_in_urls_list[0])
                        # Product folders
                        ac_product = os.path.join(ac_products_folder, product_short_name)
                        masked_product = os.path.join(masked_products_folder, product_short_name)
                        classification_product = os.path.join(classification_products_folder, product_short_name)
                    else:
                        product_short_name = "NONE"
                except Exception as e:
                    ScriptOutput2List("Product corrupted. Can't extract short name:", log_list)
                    ScriptOutput2List(str(e) + "\n", log_list)
                    excluded_products_corrupted.append(safe_file_name)

                try:
                    # -> Atmospheric Correction
                    if atmospheric_correction == True:
                        if product_short_name != "NONE":
                            ScriptOutput2List("Performing atmospheric correction with ACOLITE...", log_list) 
                            # Apply ACOLITE algorithm
                            try:
                                ACacolite(product_in_urls_list[0], ac_products_folder, os.getenv(evariables[4]), os.getenv(evariables[5]), roi)
                                corrupted_flag = 0
                            except Exception as e:
                                corrupted_flag = 1
                                ScriptOutput2List("Product might be corrupted or ACOLITE is not well configured:", log_list)
                                ScriptOutput2List(str(e), log_list)
                                ScriptOutput2List("If this is the first time running the workflow, try to clone ACOLITE manually or check credentials.", log_list)
                                # If product corrupted, ACOLITE might stop and text files will remain in main folder
                                for trash_txt in glob.glob(os.path.join(ac_products_folder, "*.txt")): 
                                    os.remove(trash_txt)
                            ScriptOutput2List("", log_list) 
                            # Organize structure of folders and files
                            log_list_append = CleanAndOrganizeACOLITE(ac_products_folder, s2l1c_products_folder, safe_file_name)
                            if os.path.exists(ac_product):
                                try:
                                    # Calculate spectral indices
                                    CalculateAllIndexes(ac_product)
                                    # Stack all and delete isolated TIF features
                                    create_features_stack(ac_product, ac_product)
                                    ScriptOutput2List("Spectral indices calculated and stacked with bands.", log_list)
                                except Exception as e:
                                    ScriptOutput2List("Product corrupted. Not all features are available:", log_list)
                                    ScriptOutput2List(str(e), log_list)
                                    excluded_products_corrupted.append(safe_file_name)
                            elif corrupted_flag == 1:
                                excluded_products_corrupted.append(safe_file_name)
                            else:
                                excluded_products_no_data_sensing_time.append(safe_file_name)
                            ScriptOutput2List("Done.\n", log_list)
                        else:
                            ScriptOutput2List("There is no S2L1C product to perform atmospheric correction.\n", log_list)
                    else:
                        ScriptOutput2List("Atmospheric Correction of product ignored.\n", log_list)
                except Exception as e:
                    ScriptOutput2List("An error occured during atmospheric correction:", log_list)
                    ScriptOutput2List(str(e) + "\n", log_list)

                try:
                    # -> Masking
                    if masking == True:
                        if (product_short_name != "NONE") and (os.path.exists(os.path.join(ac_product, product_short_name+"_stack.tif"))):
                            # Only a confirmation that you are reading the right atmospheric corrected product
                            with open(os.path.join(ac_product, "Info.txt")) as text_file:
                                safe_file_name = text_file.read()
                            ac_product_name = os.path.basename(ac_product)
                            ScriptOutput2List("Masking: " + safe_file_name + " (" + ac_product_name + ")", log_list) 
                           
                            # Reproject previous stack bounds to 4326 and provide geometry
                            ac_product_stack = os.path.join(ac_product, ac_product_name+"_stack.tif")
                            stack_epsg, stack_res, stack_bounds, stack_size = stack_info(ac_product_stack)
                            _, stack_geometry = TransformBounds_EPSG(stack_bounds, int(stack_epsg), TargetEPSG=4326)
                           
                            # -> Water mask with ESA Worldcover
                            if masking_options["use_existing_ESAwc"] == False:
                                if len(glob.glob(os.path.join(esa_wc_folder, "*.tif"))) == 0:
                                    # TS credentials
                                    ts_user = os.getenv(evariables[2])
                                    ts_pass = os.getenv(evariables[3])
                                    # Download ESA WorldCover Maps
                                    log_list_append, esa_wc_non_existing = Download_WorldCoverMaps([ts_user, ts_pass], stack_geometry, esa_wc_folder) 
                                    ScriptOutput2List("", log_list)
                                else:
                                    ScriptOutput2List("\nDownload of ESA WorldCover maps ignored, since tiles already exist.", log_list)  
                            else:
                                ScriptOutput2List("\nDownload of ESA WorldCover maps ignored.", log_list)
                                if len(glob.glob(os.path.join(esa_wc_folder, "*.tif"))) == 0:
                                    ScriptOutput2List("2-1_ESA_Worldcover folder is empty, using artificial water mask.\n", log_list) 
                                    esa_wc_non_existing = True
                                else:
                                    ScriptOutput2List("", log_list)
                                    esa_wc_non_existing = False

                            # Create masked product folder and masks folder inside
                            CreateBrandNewFolder(masked_product)
                            masks_folder = os.path.join(masked_product, "Masks")
                            CreateBrandNewFolder(masks_folder)

                            # -> Water Mask
                            ScriptOutput2List("Creating Water mask...", log_list)
                            log_list_append = Create_Mask_fromWCMaps(masked_product, esa_wc_folder, stack_epsg, stack_bounds, stack_res[0], esa_wc_non_existing, masking_options["land_buffer"])
                            ScriptOutput2List("", log_list)
                       
                            # -> Features Masks
                            if masking_options["features_mask"] == "NDWI":
                                ScriptOutput2List("Creating NDWI-based mask...", log_list)
                                log_list_append = Create_Mask_fromNDWI(ac_product, masks_folder, masking_options["threshold_values"][0], masking_options["dilation_values"][0])
                            elif masking_options["features_mask"] == "BAND8":
                                ScriptOutput2List("Creating Band8-based mask...", log_list)
                                log_list_append = Create_Mask_fromBand8(ac_product, masks_folder, masking_options["threshold_values"][1], masking_options["dilation_values"][1])
                            else:
                                ScriptOutput2List("NDWI-based or Band8-based masking ignored.", log_list)
                            ScriptOutput2List("", log_list)
                           
                            # -> Cloud Mask
                            if masking_options["cloud_mask"] == True:
                                ScriptOutput2List("Creating Cloud mask...", log_list)
                                try:
                                    log_list_append = CloudMasking_S2CloudLess_ROI_10m(ac_product, masks_folder, masking_options["cloud_mask_threshold"], masking_options["cloud_mask_average"], masking_options["cloud_mask_dilation"])
                                except Exception as e:
                                    if str(e)[-15:] == "'GetRasterBand'":
                                        ScriptOutput2List("Product corrupted. Bands are missing.", log_list)
                                        excluded_products_corrupted.append(safe_file_name)
                                    else:
                                        ScriptOutput2List(str(e) + "\n", log_list)
                                    masking_options["cloud_mask"] = False
                            else:
                                ScriptOutput2List("Cloud masking ignored.", log_list)
                            ScriptOutput2List("", log_list)
 
                            # Create final mask
                            ScriptOutput2List("Creating Final mask...", log_list)
                            user_inputs_masks = [masking_options["features_mask"], masking_options["cloud_mask"]]
                            log_list_append, final_mask_path = CreateFinalMask(masked_product, user_inputs_masks)
                            ScriptOutput2List("", log_list)

                            # Apply mask
                            if (classification_options["ml_algorithm"] == "rf") or (classification_options["ml_algorithm"] == "xgb"):
                                # Apply final mask to stack
                                ScriptOutput2List("Masking stack...", log_list)
                                mask_stack(ac_product, masked_product, filter_ignore_value=0)
                            else:
                                # For UNET apply final mask later
                                ScriptOutput2List("For Unet masking will be applied later.", log_list)
                                shutil.copy(os.path.join(ac_product, ac_product_name+"_stack.tif"), os.path.join(masked_product, ac_product_name+"_masked_stack.tif"))
                            ScriptOutput2List("Done.\n", log_list)

                            # Copy info text file
                            info_file_in = os.path.join(ac_product, "Info.txt")
                            info_file_out = os.path.join(masked_product, "Info.txt")
                            shutil.copy(info_file_in, info_file_out)
                        else:
                            ScriptOutput2List("There is no atmospheric corrected product to apply masking.\n", log_list)
                    else:
                        ScriptOutput2List("Masking of products ignored.\n", log_list)
                except Exception as e:
                    ScriptOutput2List("An error occured during masking:", log_list)
                    ScriptOutput2List(str(e) + "\n", log_list)

                try:
                    # -> Classification
                    if classification == True:
                        if (product_short_name != "NONE") and (os.path.exists(masked_product)):
                            # Only a confirmation that you are reading the right masked product
                            with open(os.path.join(masked_product, "Info.txt")) as text_file:
                                safe_file_name = text_file.read()
                            masked_product_name = os.path.basename(masked_product)
                            ScriptOutput2List("Classification: " + safe_file_name + " (" + masked_product_name + ")\n", log_list)

                            # -> Split
                            if classification_options["split_and_mosaic"] == True:
                                ScriptOutput2List("Spliting into 256x256 patches...", log_list) 
                                split_image_with_overlap(masked_product, patch_size=(256,256), overlap=0.5) # overlap of 50%
                                ScriptOutput2List("Done.\n", log_list)
                            else: 
                                ScriptOutput2List("Spliting ignored.\n", log_list)

                            # -> Classification selection
                            # Create classification product folder
                            CreateBrandNewFolder(classification_product)
                            
                            if classification_options["split_and_mosaic"] == True:
                                log_list_append = create_sc_proba_maps(os.path.join(masked_product, "Patches"), classification_product, classification_options)
                            else:
                                log_list_append = create_sc_proba_maps(masked_product, classification_product, classification_options)

                            # -> Mosaic
                            if classification_options["split_and_mosaic"] == True:
                                ScriptOutput2List("Performing mosaic of patches...", log_list) 
                                sc_maps_folder = os.path.join(classification_product, "sc_maps")
                                mosaic_patches(sc_maps_folder, sc_maps_folder, "sc_map_mosaic")
                                if (classification_options["ml_algorithm"] == "unet") and (masking == True):
                                    # Apply later mask to Unet mosaic
                                    mask_stack_later(sc_maps_folder, masked_product, filter_ignore_value=0)
                                    ScriptOutput2List("Final mask applied to Unet mosaic (sc_map).", log_list)

                                if classification_options["classification_probabilities"] == True:
                                    proba_maps_folder = os.path.join(classification_product, "proba_maps")
                                    mosaic_patches(proba_maps_folder, proba_maps_folder, "proba_map_mosaic")
                                    if (classification_options["ml_algorithm"] == "unet") and (masking == True):
                                        # Apply later mask to Unet mosaic
                                        mask_stack_later(proba_maps_folder, masked_product, filter_ignore_value=0)
                                        ScriptOutput2List("Final mask applied to Unet mosaic (proba_map).", log_list)

                                ScriptOutput2List("Done.\n", log_list)
                            else: 
                                ScriptOutput2List("Mosaic ignored.\n", log_list)

                            # Copy info text file
                            info_file_in = os.path.join(masked_product, "Info.txt")
                            info_file_out = os.path.join(classification_product, "Info.txt")
                            shutil.copy(info_file_in, info_file_out)
                        else:
                            ScriptOutput2List("There is no masked product to apply classification.\n", log_list)
                    else:
                        ScriptOutput2List("Classification of products ignored.\n", log_list)
                except Exception as e:
                    ScriptOutput2List("An error occured during classification:", log_list)
                    ScriptOutput2List(str(e) + "\n", log_list)

                # Delete processing folders and files
                try:
                    # -> Delete original products
                    if delete["original_products"] == True:
                        delete_folder(safe_file_path)
                        ScriptOutput2List("Original products deleted.\n", log_list)

                    # -> Delete some intermediate 
                    if delete["some_intermediate"] == True:
                        delete_intermediate(ac_product, masked_product, classification_product, mode="some")
                        ScriptOutput2List("Some intermediate folders and files deleted.\n", log_list)

                    # -> Delete all intermediate
                    if delete["all_intermediate"] == True:
                        delete_intermediate(ac_product, masked_product, classification_product, mode="all")
                        ScriptOutput2List("All intermediate folders and files deleted.\n", log_list)
                except Exception as e:
                    ScriptOutput2List("An error occurred while deleting folders and files:", log_list)
                    ScriptOutput2List(str(e) + "\n", log_list)
           
    else:
        ScriptOutput2List("Stream Processing ignored.\n", log_list)


    
    # STATISTICS ###########################################################################
    number_found_products = len(urls_list)
    number_excluded_products_old_format = len(excluded_products_old_format)
    number_excluded_products_no_data_sensing_time = len(excluded_products_no_data_sensing_time)
    number_coah_lta_products = len(coah_lta_products)
    number_excluded_products_corrupted = len(excluded_products_corrupted)
    number_processed_products = number_found_products - (number_excluded_products_old_format + \
        number_excluded_products_no_data_sensing_time + number_coah_lta_products + number_excluded_products_corrupted)
    
    # Products found in ROI for selected Sensing Period
    ScriptOutput2List("Number of products found for selected ROI and Sensing Period: " + str(number_found_products), log_list)
    # Products processed in ROI for selected Sensing Period
    ScriptOutput2List("Number of products processed for selected ROI and Sensing Period: " + str(number_processed_products), log_list)
    # Products excluded (old format)
    ScriptOutput2List("Number of products excluded (old format): " + str(number_excluded_products_old_format), log_list)
    if number_excluded_products_old_format != 0:
        excluded_products_old_format = "\n".join(excluded_products_old_format)
        ScriptOutput2List(excluded_products_old_format, log_list)  
    # Products excluded (ROI falls 100% on no data side of partial tile or scene have same sensing time)
    ScriptOutput2List("Number of products excluded (100% no data or same sensing time): " + str(number_excluded_products_no_data_sensing_time), log_list)
    if number_excluded_products_no_data_sensing_time != 0:
        excluded_products_no_data_sensing_time = "\n".join(excluded_products_no_data_sensing_time)
        ScriptOutput2List(excluded_products_no_data_sensing_time, log_list)
    # Products COAH LTA (product not available for retrieval from LTA)
    ScriptOutput2List("Number of products not available (COAH Long Term Archive): " + str(number_coah_lta_products), log_list)
    if number_coah_lta_products != 0:
        coah_lta_products = "\n".join(coah_lta_products)
        ScriptOutput2List(coah_lta_products, log_list)
    # Corrupted products (some bands or metadata not available during download)
    ScriptOutput2List("Number of corrupted products: " + str(number_excluded_products_corrupted), log_list)
    if number_excluded_products_corrupted != 0:
        excluded_products_corrupted = "\n".join(excluded_products_corrupted)
        ScriptOutput2List(excluded_products_corrupted, log_list)

else:
    print("Failed to pré-start script.\n")

# END ######################################################################################

# Finish time of POS2IDON
POS2IDON_timef = time.time()
# Duration of POS2IDON
POS2IDON_timep = int(POS2IDON_timef - POS2IDON_time0)

ScriptOutput2List("\nPS2IDON total time: "+str(POS2IDON_timep)+" seconds.\n", log_list)

# Save log
ScriptOutputs2LogFile(log_list, "4_LogFile")

print("\nPOS2IDON CLOSED.\n")




