#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
User Inputs.
Credentials must be modified in the hidden .env file.

@author: AIR Centre
"""

# SEARCH ###################################################################################

# Query Sentinel-2 L1C Products in the services catalogue and creates a list of products 
# that will be saved inside s2l1c_products_folder.
# If False, this step will be ignored and the products list must exist inside s2l1c_products_folder
# for the download to work.
# Other inputs besides bool will stop the pré-start.
search = False

# Search service:
# "CDSE" (Copernicus Data Space Ecosystem - the new ESA service).
# "COAH" (Copernicus Open Access Hub - better for recent data and near real time application). 
# "GC" (Google Cloud - better for old data and long term application).
# "CDSE" (Copernicus Data Space Ecosystem - the new ESA service). Full archive soon!
# Other inputs besides string will stop the pré-start.
# Other strings will be considered as "CDSE".
service = "GC"

# Search service options:
# Other inputs besides dictionary with correct values will stop the pré-start.
                   # Filter specific combination from the S2L1CProducts_URLs.txt, 
                   # e.g. "T31UDU", "R094_T31UDU" or "R094"
                   # String, use "" to ignore.
service_options = {"filter": "",                  
                   # Number of Long Term Archive attempts for COAH service.
                   # Minimum is 1 attempt. Script waits 60 seconds between each attempt.
                   "lta_attempts": 5,
                   # If first time using CDSE, generate an acess token. 
                   # Needs to have credentials or refresh token inside .env file.
                   # Access token will be saved inside same .env file. 
                   "generate_token": True} 

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
sensing_period = ('20200917', '20200919')

# PROCESSING ###############################################################################

# Includes download, atmospheric correction, masks and classification.
# URLs file created by SEARCH must exist.
# You can also create a dummy URLs list file named S2L1CProducts_URLs.txt, inside place dummy
# URLs: dummy/NAMEOFPRODUCT1.SAFE
#       dummy/NAMEOFPRODUCT2.SAFE
# The PROCESSING needs to have S2L1C products that correspond to the URLs file, 
# even if you have already atmospheric corrected products.
# Other inputs besides bool will stop the pré-start.
processing = True


# Download is done for each url. Use SEARCH if needed.
# True - Downloads Sentinel-2 L1C products from the services using URLs file. 
# False - Does not download products, it assumes you downloaded already.
# Other inputs besides bool will stop the pré-start.
download = False


# Atmospheric correction of Sentinel-2 L1C Products using ACOLITE. 
# True - AC products inside s2l1c_products_folder.
# False - Does not AC products, it assumes they exist already.
# Other inputs besides bool will stop the pré-start.
atmospheric_correction = False


# Apply masks to the atmospheric corrected product.
# True - Creates masks that are applied or will be applied (UNet) to AC products inside ac_products_folder.
# False - Assumes you have already the masks. Note: This does not mean that application of masks will be ignored.
# Other inputs besides bool will stop the pré-start.
masking = True

# Masking options.
# Other inputs besides dictionary with correct values will stop the pré-start.
# Ignore application of masks (classify entire image) by:
# "use_existing_ESAwc": True and leave 2-1_ESA_Worldcover folder empty.
# "features_mask": None
# "cloud_mask": False
                   # Use existing ESA WorldCover Tiles that are inside 2-1_ESA_Worldcover to create water mask.
                   # If False, it will download the tiles.
masking_options = {"use_existing_ESAwc": True,  
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
# True - Classification using data from masked_products_folder.
# False - Ignores classification.
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
                          # Unet Julia is recognized by the model extension .bson  
                          "ml_algorithm": "rf",
                          # Path to the folder containing the machine learning model.
                          "model_path": "configs/MLmodels/RF_Model_Example_MARIDA",
                          # Model_type:
                          # "sk" for original model created with scikit.
                          # "CPUpt" for model converted to pytorch and processed on CPU.
                          # "GPUpt" for model converted to pytorch and processed on GPU. Max size of model limited by GPU memory.
                          # None for Unet models.
                          "model_type": "sk",
                          # Number of classification classes. Change when changing model.
                          "n_classes": 11,
                          # Tuple of features to consider, must match the ones used during model train. Change when changing model.
                          # Features available are ('B01', 'B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B8A', 'B11', 'B12', 'NDVI', 'FAI', 'FDI', 'SI', 'NDWI', 'NRD', 'NDMI', 'BSI') or ('B01', 'B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B8A', 'B11', 'B12')
                          # For Unet use only the 11 bands as features
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
