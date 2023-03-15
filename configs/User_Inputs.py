#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
User Inputs.
Credentials must be modified in the hidden .env file.

@author: AIR Centre
"""

# SEARCH PRODUCTS ##########################################################################

# Query Sentinel-2 L1C Products in the services catalogue and creates a list of products 
# that will be saved inside s2l1c_products_folder.
# If False, this step will be ignored and the products list must exist inside s2l1c_products_folder
# for the download to work.
# Other inputs besides bool will stop the pré-start.
search = True

# Search service:
# "COAH" (Copernicus Open Access Hub - better for recent data and near real time application). 
# "GC" (Google Cloud - better for old data and long term application).
# "CDSE" (Copernicus Data Space Ecosystem) - NOT YET AVAILABLE.
# Other inputs besides string will stop the pré-start.
# Other strings will be considered as "CDSE".
service = "GC"

# Region Of Interest (ROI): 
# SentinelHub EOBrowser (https://apps.sentinel-hub.com/eo-browser/) format. 
# Also used by ACOLITE. If ROI has limits outside the product, ACOLITE will ignore.
# Other inputs besides dictionary with correct values will stop the pré-start.
roi = {"type":"Polygon","coordinates":[[[-88.308792,15.660726],[-88.308792,15.928978],[-88.040314,15.928978],[-88.040314,15.660726],[-88.308792,15.660726]]]}

# Near real time sensing period:
# Uses yesterday as start date and today as end date. 
# sensing_period is ignored.
# Other inputs besides bool will stop the pré-start.
nrt_sensing_period = False

# Sensing period of interest:
# Used only if nrt_sensing_period = False.
# (StartDate, EndDate).
# Other inputs besides tuple with correct values will stop the pré-start.
sensing_period = ('20200918', '20200918')

# STREAM PROCESSING ########################################################################

# Includes stream download, atmospheric correction, masks and classification.
# URLs file created by SEARCH PRODUCTS must exist.
# You can also create a dummy URLs list file named S2L1CProducts_URLs.txt, inside place dummy
# URLs: dummy/NAMEOFPRODUCT1.SAFE
#       dummy/NAMEOFPRODUCT2.SAFE
# The STREAM PROCESSING needs to have S2L1C products that correspond to the URLs file, 
# even if you have already atmospheric corrected products.
# Other inputs besides bool will stop the pré-start.
stream_processing = True


# Download is done in stream fashion. Use SEARCH if needed.
# Download Sentinel-2 L1C Products from the GC or COAH services using URLs file. 
# Other inputs besides bool will stop the pré-start.
download = True

# Download options.
# Other inputs besides dictionary with correct values will stop the pré-start.
                    # Number of Long Term Archive attempts for COAH service.
                    # Minimum is 1 attempt. Script waits 60 seconds between each attempt.
download_options = {"lta_attempts": 2}  


# Atmospheric correction of Sentinel-2 L1C Products using ACOLITE. 
# s2l1c_products_folder must exist with data.
# Other inputs besides bool will stop the pré-start.
atmospheric_correction = True


# Apply masks to the atmospheric corrected product.
# ac_products_folder must exist and have data.
# Other inputs besides bool will stop the pré-start.
masking = True

# Masking options.
# Other inputs besides dictionary with correct values will stop the pré-start.
                   # Use existing ESA WorldCover Tiles that are inside 2-1_ESA_Worldcover to create water mask.
                   # If False, it will download the tiles.
                   # Ignore water mask by using option True without tiles in the 2-1_ESA_Worldcover folder.
masking_options = {"use_existing_ESAwc": False,  
                   # Buffer size applied to land, 0 to ignore.
                   "land_buffer": 0,
                   # Apply mask based on 'NDWI' or 'BAND8' (features), None to ignore.
                   "features_mask": 'BAND8',
                   # NDWI and Band8 thresholds
                   "threshold_values": [0.5, 0.01],
                   # NDWI and Band8 dilations (number of iteration must be equal or greater then 1)
                   "dilation_values": [6, 2],
                   # Create cloud mask using s2cloudless, false to ignore.
                   "cloud_mask": True,
                   # Cloud probability threshold, pixels with cloud probability above this threshold are masked as cloudy pixels.
                   "cloud_mask_threshold": 0.4,
                   # Size of the disk in pixels to performe convolution (averaging probability over pixels).
                   "cloud_mask_average": 2,
                   # Size of the disk in pixels to performe dilation.
                   "cloud_mask_dilation": 1
                   }


# Perform classification on masked products.
# masked_products_folder must exist and have data.
# Other inputs besides bool will stop the pré-start.
classification = True

# Classification options.
# Other inputs besides dictionary with correct values will stop the pré-start.                       
                          # Split full image into 256x256 patches and consider each one during classification.
                          # Mosaic all patches into single image after classification.
classification_options = {"split_and_mosaic": False,
                          # Outputs TIF file with the class probability for each pixel.
                          "classification_probabilities": False,
                          # Machine Learning algorithm:
                          # "rf" for Random Forest. 
                          # "xgb" for XGBoost. 
                          # "unet" for Unet. This model needs split_and_mosaic option True.
                          "ml_algorithm": "rf",
                          # Path to the folder containing the machine learning model.
                          "model_path": "configs/MLmodels/RF_Model_Example_MARIDA",
                          # Model_type:
                          # "sk" for original model created with scikit.
                          # "CPUpt" for model converted to pytorch and processed on CPU.
                          # "GPUpt" for model converted to pytorch and processed on GPU. Max size of model limited by GPU memory.
                          # None for Unet models.
                          "model_type": "sk",
                          # Number of classification classes. 6 or 11
                          "n_classes": 11,
                          # Tuple of features to consider, must match the ones used during model train.
                          # Features available are ('B01', 'B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B8A', 'B11', 'B12', 'NDVI', 'FAI', 'FDI', 'SI', 'NDWI', 'NRD', 'NDMI', 'BSI') or ('B01', 'B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B8A', 'B11', 'B12', 'NDVI', 'FDI', 'NDWI', 'NDMI')
                          "features": ('B01', 'B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B8A', 'B11', 'B12', 'NDVI', 'FAI', 'FDI', 'SI', 'NDWI', 'NRD', 'NDMI', 'BSI'),
                          # Only used for Unet models. Number of hidden channels.
                          "n_hchannels": 16,
                          # Only used for Unet models. Mean value for each feature.
                          "features_mean": [0.05197577, 0.04783991, 0.04056812, 0.03163572, 0.02972606, 0.03457443, 0.03875053, 0.03436435, 0.0392113,  0.02358126, 0.01588816],
                          # Only used for Unet models. Standard Deviation value for each feature.
                          "features_std": [0.04725893, 0.04743808, 0.04699043, 0.04967381, 0.04946782, 0.06458357, 0.07594915, 0.07120246, 0.08251058, 0.05111466, 0.03524419]
                          }


# Delete processed folders and files:
# Other inputs besides dictionary with correct values will stop the pré-start.
          # Delete original products:
          # Deletes original product after each processing.
delete = {"original_products": False,
          # Delete some intermediate after each processing - Recommended:
          # Deletes Surface_Reflectance_Bands, Top_Atmosphere_Bands, masked Patches,
          # Mosaics and single intermediate files in both sc_maps and proba_maps.
          # But DOESN'T, delete atmospheric correction stack, Masks, masked stack.
          "some_intermediate": False,
          # Delete all intermediate after each processing - Not Recommended:
          # Only final results available.
          # Deletes Surface_Reflectance_Bands, Top_Atmosphere_Bands, masked Patches,
          # Mosaics and single intermediate files in both sc_maps and proba_maps.
          # BUT ALSO, deletes atmospheric correction stack, Masks, masked stack.
          "all_intermediate": False
          }


# FOLDERS NAMES ############################################################################

# Download folder:
# Folder where the URLs file and downloaded S2L1C products will be saved.
# Other inputs besides string will stop the pré-start.
s2l1c_products_folder = "0_S2L1C_Products"

# Atmospheric correction folder:
# Folder where the S2 atmospherically corrected bands will be saved. 
# Other inputs besides string will stop the pré-start.
ac_products_folder = "1_Atmospheric_Corrected_Products"

# Masking folder:
# Folder where the masked products will be saved. The water, features and cloud masks will also
# be saved in this folder.
# Other inputs besides string will stop the pré-start.
masked_products_folder = "2_Masked_Products"

# Classification folder:
# Folder where the final classification results will be saved.
# Other inputs besides string will stop the pré-start.
classification_products_folder = "3_Classification_Results"
