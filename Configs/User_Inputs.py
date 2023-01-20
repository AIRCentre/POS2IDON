#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
User Inputs.
Credentials must be modified in the hidden .env file due to security.

@author: AIR Centre
"""

# WORKFLOW OPTIONS ----------------------------------------------------------------------------------------------------------------------------------------------------------

# PERFORM SEARCH
# The True option enables to query Sentinel-2 L1C Products in the Google Cloud Service catalogue or Copernicus Open Access Hub and produce a list of products saved in 'S2L1C_Products/S2L1CProducts_URLs.txt'
# If the False option is used, this step will be ignored and the S2L1CProducts_URLs.txt should be placed in the S2L1CproductsFolder.
# Boolean.
Search = True

# PERFORM PROCESSING
# The True option enables the downloading and processing steps of each Sentinel-2 L1C Products once at the time.
# If the False option is used, all the following steps will be ignored.
# Boolean.
Processing = True

# PERFORM DOWNLOAD
# The True option enables to Download Sentinel-2 L1C Products from the Google Cloud Service or Copernicus Open Access Hub.
# If the False option is used, this step will be ignored and the S2L1CproductsFolder must contain data.
# Boolean.
Download = True

# PERFORM ATMOSPHERIC CORRECTION
# The True option enables to AC Sentinel-2 L1C Products. 
# If the False option is used, this step will be ignored and ACOLITEoutputsFolder must contain data.
# Boolean.
AtmosCorrect = True

# CALCULTE INDICES FROM NOT MASKED ACOLITE BANDS
# The True option enables to calculate indices from acolite bands (not masked). 
# If the False option is used, this step will be ignored.
# Boolean.
CalculateNotMaskedIndices = True

# PERFORM MIDDLE STEPS
# The True option enables to create masks, apply masks and calculate indices for Sentinel-2 images. 
# If the False option is used, this step will be ignored and MaskingProduct Folder & MaskedProduct Folder must contain data.
# Boolean.
MiddleSteps = True

# PERFORM CLASSIFICATION
# The True option enables to perform the classification of Sentinel-2 images. 
# If the False option is used, this step will be ignored and SC map & PROBA map will not be created.
# Boolean.
Classify = True

# STORAGE OPTIONS ----------------------------------------------------------------------------------------------------------------------------------------------------------

# DELETE NOT NECESSARY INTERMEDIATED FILES
# The True option enables, to delete all ACOLITE outputs (folders are kept) and masked bands and indices in the Results_MaskedBands-Indices-SCmaps folder (SCmap and PROBAmap are kept).
# If the False option is used, this step will be ignored and the file is stored in the S2L1C Product Folder.
# Boolean.
DeleteIntermediateFiles = False

# DELETE ORIGINAL PRODUCTS
# The True option enables to delete the SAFE product folder after the image is processed. 
# If the False option is used, this step will be ignored and the file is stored in the S2L1C Product Folder.
# Boolean.
DeleteOriginalProduct = False


# SEARCH AND DOWNLOAD OPTIONS --------------------------------------------------------------------------------------------------------------------------------------------------

# REGION OF INTEREST 
# SentinelHub EOBrowser (https://apps.sentinel-hub.com/eo-browser/) format. If ROI has limits outside the product, ACOLITE will ignore.
# Dictionary.
# Example: ROI = {"type":"Polygon","coordinates":[[[-88.308792,15.660726],[-88.308792,15.928978],[-88.040314,15.928978],[-88.040314,15.660726],[-88.308792,15.660726]]]}
ROI = {"type":"Polygon","coordinates":[[[-88.308792,15.660726],[-88.308792,15.928978],[-88.040314,15.928978],[-88.040314,15.660726],[-88.308792,15.660726]]]}

# SENSING PERIOD OF INTEREST
# (StartDate, EndDate). Needed if StartDateYesterday = False. 
# Tuple of strings as ('YYYYMMDD','YYYYMMDD').
# Example: SensingPeriod = ('20200918', '20200918')
SensingPeriod = ('20200918', '20200918')

# RECENT SENSING PERIOD
# Use yesterday as start date and today as end date. SensingPeriod is ignored. Google Cloud download service is ignored.
# Boolean.
StartDateYesterday = False

# DOWNLOAD SERVICE 
# COAH (Copernicus Open Access Hub - better for recent data and near real time application) or GC (Google Cloud - better for old data and long term application)
# String: "COAH" or "GC"
DownloadService = "GC"


# MASK OPTIONS ----------------------------------------------------------------------------------------------------------------------------------------------------------

# ESA WORLDCOVER
# Use existant ESA WorldCover Tiles that are inside ESAwcFolder to create water mask. The downloading is ignored.
# Boolean.
UseExistantESAwc = False

# LAND BUFFER SIZE
# Buffer size applied to land, if 0 is used the buffer step is ignored.
# Integer.
BufferSize = 0

# NDWI or BAND 8 MASKING
# Create NDWI or BAND8 based mask. 
# Select type of masking. 'NDWI' , 'BAND8' , None 
Select_NDWI_or_BAND8_Masking = 'BAND8'
# NDWI threshold and dilation (number of iteration must be equal or greater then 1) value to create mask
NDWIthreshold=0.5 ; NDWIDilation_Size=6
# Band 8 threshold and dilation (number of iteration must be equal or greater then 1) value to create mask
Band8threshold=0.01 ; Band8Dilation_Size=2

# CLOUDS
# Create cloud mask using s2cloudless. 
# Boolean.
CloudMaskingS2cloudless = True
# Specify the cloud probability threshold. pixels with cloud probability above this threshold are masked as cloudy pixels. 
S2CL_Threshold=0.4 
# Size of the disk in pixels for performing convolution (averaging probability over pixels).
S2CL_Average=2
#Size of the disk in pixels for performing dilation.
S2CL_Dilation=1

# NEGATIVE REFLECTANCES
# Remove pixels with negative reflectances from masked bands. 
# Boolean.
RemoveNegativeReflectances = True


# CLASSIFICATION -------------------------------------------------------------------------------------------------------------------------------------------------------

# MODEL FOLDER LOCATION
# Location of the scikit model (.pkl) and pytorch conversion (.zip) or julia model
# The name of the model will be used to select the features (bands and indices) during classification.
# String.
#ModelFolderPath = "Configs/MLmodels/YourModelFolder"
ModelFolderPath = "Configs/MLmodels/RF_Model_Example_MARIDA"

# Machine Learning Algorithm TYPE (only for python models)
# Specify if the model is "rf" for random forest | "xgb" for xgboost
MLAlgorithm = "rf"

# MODEL TYPE (only for python models)
# CPUpt for model converted to pytorch and processed on CPU.
# GPUpt for model converted to pytorch and processed on GPU. Max size of model limited by GPU memory. Doesnt work on macOS. 
# sk for original model created with scikit, other inputs will be consider as sk.
# String.
ModelType = "sk"

# CLASS PROBABILITIES (only for python)
# Outputs .tif file with the class probability for each pixel predicted by the model
# Boolean.
ClassProba = True

# PERFORM CLASSIFICATION IN JULIA (test-phase)
# Boolean.
ClassifyinJulia = False
# Indicate Julia model name
RF_model_jl = "YourModel.jld2"

# FOLDERS NAMES -----------------------------------------------------------------------------------------------------------------------------------------------------

# Folder where the downloaded S2-L1C products will be saved. 
# String.
S2L1CproductsFolder = 'S2L1C_Products'

# Folder where the S2 atmospherically corrected bands will be saved. 
# String.
ACOLITEoutputsFolder = 'ACOLITE_Outputs'

# Folder where the ESA WorldCover maps will be saved.
# String.
ESAwcFolder = 'ESAwc_Tiles'

# Folder where the masking will be saved. 
# String.
MaskingProductsFolder = 'Masking_Outputs'
MaskedProductsFolder = 'Masked_Outputs'

# Folder where the final results (masked bands, indices and scene classification map) will be saved. 
# String.
ResultsFolder = 'Results_SCmaps'