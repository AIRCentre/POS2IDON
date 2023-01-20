#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
The Pipeline_for_ocean_features_and_plastic_detection_with_S2 is the main script that classifies pixels in a Sentinel-2 image and detects marine litter. It uses machine learning models trained 
with spectral signatures and spectral indices data.

Atlantic International Research Centre (AIR Centre - EO LAB), Terceira Island, Azores, Portugal.

@author: AIR Centre
"""


### Pré-Start ##################################################################################################################################################################################################################################################
# List of script outputs to save as .txt log file - Important for script running in server
LogList = []
# Pré-start functions
try:
    print("\n\nImporting Pré-start functions...")
    from Functions.PreStart import *
    print("Done.\n")
except Exception as e:
    print(str(e) + '\n')

# Clone important modules from GitHub (FeLS and ACOLITE)
try:
    CloneModulesFromGitHub("Configs")
except Exception as e:
    print(str(e) + '\n')

### Import Libraries ###########################################################################################################################################################################################################################################
# Environment (don't change order of installation):
# conda create -n Pipeline-Env python=3.9
# conda activate Pipeline-Env
# conda install -c conda-forge gdal=3.5.0
# conda install -c conda-forge geopandas=0.11.1
# conda install -c conda-forge lightgbm=3.3.2 # Because of s2cloudless
# pip install python-dotenv==0.20.0
# pip install sentinelsat==1.1.1
# pip install zipfile36==0.1.3
# pip install netCDF4==1.5.8
# pip install pyproj==3.3.1
# pip install scikit-image==0.19.2
# pip install pyhdf==0.10.5
# pip install --extra-index-url https://artifactory.vgt.vito.be/api/pypi/python-packages/simple terracatalogueclient==0.1.11
# pip install matplotlib==3.5.2
# pip install pandas==1.4.3
# pip install scikit-learn==1.1.1
# pip install ubelt==1.1.2
# pip install s2cloudless==1.6.0
# pip install rasterio==1.3.0.post1
# pip install hummingbird-ml==0.4.5
# pip install xgboost


# Notes:
# The reason of Segmentation Fault error is still unknown to us, but it is related with the environment.
# Installation of conda install -c conda-forge cudatoolkit=11.6 ignored. On macOS, ModelType = "GPUpt" will not work.
# conda install -c pytorch pytorch=1.12.1, conda install -c pytorch torchvision=0.13.1 and conda install -c pytorch torchaudio=0.12.1 crashes ACOLITE on macOS due to numpy version. 


try:
    ScriptOutput2List("Importing Libraries...", LogList)
    import os
    from dotenv import load_dotenv
    import glob
    from osgeo import gdal
    import time
    ScriptOutput2List("Done.\n", LogList)
except Exception as e:
    ScriptOutput2List(str(e) + "\n", LogList)

# Start time of processing
Ptime0 = time.time()

### Import Defined Functions #################################################################################################################################################################################################################################
try:
    ScriptOutput2List("Importing Defined Functions...", LogList)
    from Functions.Auxiliar import * 
    from Functions.S2L1CProcessing import *
    from Functions.S2L2Processing import *
    from Functions.Masking import *
    from Functions.SpectralIndices import *
    from Functions.Classification import *
    ScriptOutput2List("Done.\n", LogList)
except Exception as e:
    ScriptOutput2List(str(e) + "\n", LogList)

### User Inputs ###############################################################################################################################################################################################################################################
try:
    ScriptOutput2List("Importing User Inputs...", LogList)
    from Configs.User_Inputs import *
    ScriptOutput2List("Done.\n", LogList)
except Exception as e:
    ScriptOutput2List(str(e) + "\n", LogList)

### Import Credentials #########################################################################################################################################################################################################################################
# Requires .env file with  credentials inside Configs folder
try:
    ScriptOutput2List("Importing Credentials...", LogList)
    # Path of .env file
    Basepath = os.getcwd()
    EnvPath = os.path.join(Basepath,"Configs/Environments/.env")
    # Environment variables
    Evariables = ("COAHuser", "COAHpassword", "TSuser", "TSpassword", "EDuser", "EDpassword")
    load_dotenv(EnvPath)
    ScriptOutput2List("Done.\n", LogList)
except Exception as e:
    ScriptOutput2List(str(e) + "\n", LogList)


### Search Sentinel-2 products ###########################################################################################################################################################################################################
# Search option used if you want to search products andrea.giusti andrea.giusti
if Search == True:
    #Create folder to store products
    CreateBrandNewFolder(S2L1CproductsFolder)
    
    # Sensing Period using Yesterday as Start Date Option - Used to run in a server as near-real time.
    if StartDateYesterday == True:
        ScriptOutput2List("Using Yesterday date as Start Date...")
        SensingPeriod = NearRealTimeSensingDate()
    
    # Search and Download products using Google Cloud or COAH
    try:
        if DownloadService == "GC":
            LogListToAppend = CollectDownloadLinkofS2L1Cproducts_GC(ROI, SensingPeriod, S2CatalogueFolder="Configs")
        else:
            LogListToAppend = CollectDownloadLinkofS2L1Cproducts_COAH(os.getenv(Evariables[0]), os.getenv(Evariables[1]), ROI, SensingPeriod)
        LogList = LogList + LogListToAppend
    except Exception as e:
        ScriptOutput2List(str(e) + "\n", LogList)

else:
    ScriptOutput2List("Ignoring the Search of Products.\n", LogList)

### Stream processing of collected Sentinel-2 products ###########################################################################################################################################################################################################
# Processing option if True, each single product is downloaded and processed, once done the next product is downloaded and processed
#                   if False processing is ignored

# Create outputs folders:
if AtmosCorrect == True:
    # Create folder to save ACOLITE correction
    CreateBrandNewFolder(ACOLITEoutputsFolder)
if MiddleSteps == True:
    # Create folder to save MIDDLE STEPS outputs
    CreateBrandNewFolder(MaskingProductsFolder)
    CreateBrandNewFolder(MaskedProductsFolder)
if UseExistantESAwc == False:
    # Create brand new folder to save downloaded WorldCover maps
    CreateBrandNewFolder(ESAwcFolder)
if Classify == True:
     # Create brand new folder to save results (masked bands, indices, supervised classification maps)
    CreateBrandNewFolder(ResultsFolder)

####################################################################################################################################################################################
if Processing == True:           

    # Read S2L1CProducts_URLs.txt file and create list         
    ListS2L1CProducts_URLs= open('S2L1C_Products/S2L1CProducts_URLs.txt').read().splitlines()
    if len(ListS2L1CProducts_URLs) == 0:
        ScriptOutput2List("List of product url is empty.\n", LogList)
    else:
        ScriptOutput2List("____________________________________ Start Downloading and Processing____________________________________\n", LogList)
        
        # Create lists of excluded products names to print in the log file
        ListofExcludedProducts_OldFormat =[]
        ListofExcludedProducts_NoData_SensingTime =[]
        Listof_COAH_LTA_Products =[]

        # Start loop on list of url download link retrieved from Google Cloud Service or COAH
        for i,url in enumerate (ListS2L1CProducts_URLs):
            try:
                ScriptOutput2List("(" + str(i+1) +  "/" + str(len(ListS2L1CProducts_URLs)) + ")\n", LogList)
                # Get SAFE file name from url link
                SAFEFileName = url.split('/') [-1]
                # Download product using Google Cloud Service or COAH URL
                if Download == True:
                    if DownloadService == 'GC':
                        LogListToAppend = DownloadTile_from_URL_GC(url,S2L1CproductsFolder)
                        # Check if OPER file was excluded when using Google Cloud Service
                        if not os.path.exists("".join(glob.glob(os.path.join(Basepath,S2L1CproductsFolder,SAFEFileName))).replace("\\","/")):
                            ListofExcludedProducts_OldFormat.append(url)
                            ScriptOutput2List("The scene is in the redundant OPER old-format (before Nov 2016).Product excluded.\n", LogList)
                            ScriptOutput2List("_________________________________________________________________________________________________________\n", LogList)
                            continue
                    else:
                        LogListToAppend = DownloadTile_from_URL_COAH(os.getenv(Evariables[0]), os.getenv(Evariables[1]),url,S2L1CproductsFolder)
                        # Check if file is not retrievable from the COAH Long Term Archive
                        if not os.path.exists("".join(glob.glob(os.path.join(Basepath,S2L1CproductsFolder,SAFEFileName))).replace("\\","/")):
                            Listof_COAH_LTA_Products.append(url)
                            ScriptOutput2List("Download of " + SAFEFileName + " from Long Term Archive may not be available.\nTry Google Cloud Service instead.\n", LogList)
                            ScriptOutput2List("_________________________________________________________________________________________________________\n", LogList)
                            continue
                    LogList = LogList + LogListToAppend
                else:
                    ScriptOutput2List("Ignoring the downloading of Products. S2L1C Product Folder must contain data.\n", LogList)

                # Extract Product Short Name from SAFE file metadata using same formatting as Acolite
                SAFEProductFile= os.path.join(S2L1CproductsFolder,SAFEFileName)
                ShortProductName = Extract_ACOLITE_name_from_SAFE(SAFEProductFile) 
                # AtmosCorrect option used if you want to atmospherically correct the product
                if AtmosCorrect == True:
                    # Atmospheric Correction using ACOLITE
                    ProductsToAC = glob.glob(os.path.join(S2L1CproductsFolder,SAFEFileName))
                    ScriptOutput2List("Using ACOLITE to AC...", LogList)
                    # Apply ACOLITE algorithm
                    ACacolite(ProductsToAC, ACOLITEoutputsFolder, os.getenv(Evariables[4]), os.getenv(Evariables[5]), ROI)
                    # Organize structure of folders and files
                    LogListToAppend = CleanAndOrganizeACOLITE(ACOLITEoutputsFolder,S2L1CproductsFolder,SAFEFileName)
                    LogList = LogList + LogListToAppend
                    ScriptOutput2List("Done.\n", LogList)
                    # Check if SAFE file was deleted because only no data in ROI or same sensing time
                    if os.path.exists(os.path.join(S2L1CproductsFolder,SAFEFileName)):
                        if CalculateNotMaskedIndices == True:
                            # Calculate and Save Indices (Must match indices used on ML model)
                            ScriptOutput2List("Calculating not masked indices for " + ShortProductName, LogList)
                            CalculateAllIndexes(ACOLITEoutputsFolder, ShortProductName)
                            ScriptOutput2List("Done.\n", LogList)
                    else:
                        ListofExcludedProducts_NoData_SensingTime.append(url)
                else:
                    ScriptOutput2List("Ignoring the Atmospheric Correction of Products. ACOLITE Product Folder must contain data.\n", LogList)
                
                # MiddleSteps option used if you want to create masks, apply masks and calculate spectral indices
                if MiddleSteps == True:
                    ### Download ESA WorldCover Maps and Create Masks (Water, NDWI or Band8 and Cloud). Apply them to all bands ###
                    # Check if SAFE file was deleted because only no data in ROI or duplicate
                    if os.path.exists(os.path.join(S2L1CproductsFolder,SAFEFileName)):
                        ScriptOutput2List("Creating Masks for " + ShortProductName + ":", LogList)
                        # Select Driver
                        Driver = gdal.GetDriverByName("GTiff")
                        # User Inputs for masking
                        UInFinalMask = [Select_NDWI_or_BAND8_Masking, CloudMaskingS2cloudless]
                        # Use one of the acolite output bands as reference.
                        ACOLITEProductFile = os.path.join(ACOLITEoutputsFolder,ShortProductName)
                        B2refPath = os.path.join(ACOLITEProductFile, "B02.tif")
                        B2refRaster = gdal.Open(B2refPath)
                        B2refProjection, B2refResolution, B2refBounds, B2refSize = Raster_MainInfo(B2refRaster)
                        # Reproject previous band bounds to 4326 and provide geometry
                        B2refBounds4326, B2geometry = TransformBounds_EPSG(B2refBounds, int(B2refProjection), TargetEPSG=4326)

                        if UseExistantESAwc == False:
                            if len(os.listdir(ESAwcFolder)) == 0:
                                # TS credentials
                                TSuser = os.getenv(Evariables[2])
                                TSpass = os.getenv(Evariables[3])
                                # Download ESA WorldCover Maps
                                LogListToAppend,ESAwcNonExistTile = Download_WorldCoverMaps([TSuser, TSpass], B2geometry, ESAwcFolder) 
                                LogList = LogList + LogListToAppend
                            else:
                                ScriptOutput2List("Ignoring download of ESA WorldCover maps, since tile already exists.", LogList)
                        else:
                            ScriptOutput2List("Ignoring download of ESA WorldCover maps, since tile already exists.", LogList)
                            if len(glob.glob(os.path.join(ESAwcFolder, "*.tif"))) == 0:
                                ScriptOutput2List("Your folder is EMPTY, an artificial water mask will be generated. Land may not be masked out.", LogList) 
                                ESAwcNonExistTile = True
                            else:
                                ESAwcNonExistTile = False
                        
                        # Create brand new product folder to save Masking files
                        ProductMaskingFolder = os.path.join(MaskingProductsFolder, ShortProductName)
                        CreateBrandNewFolder(ProductMaskingFolder)

                        # Create WATER Mask
                        ScriptOutput2List("Creating WATER Mask...", LogList)
                        LogListToAppend = Create_Mask_fromWCMaps(ESAwcFolder, B2refProjection, B2refBounds, 10, ProductMaskingFolder, ESAwcNonExistTile, BufferSize)
                        LogList = LogList + LogListToAppend

                        # Create or ignore Mask based on NDWI to avoid classifing only-water pixels
                        if Select_NDWI_or_BAND8_Masking == 'NDWI':
                            ScriptOutput2List("Creating NDWI-based Mask...", LogList)
                            LogListToAppend = Create_Mask_fromNDWI(ACOLITEProductFile, ProductMaskingFolder,NDWIthreshold,NDWIDilation_Size)
                            LogList = LogList + LogListToAppend
                        elif Select_NDWI_or_BAND8_Masking =='BAND8':
                            ScriptOutput2List("Creating BAND8-based Mask...", LogList)
                            LogListToAppend = Create_Mask_fromBand8(ACOLITEoutputsFolder,ShortProductName, ProductMaskingFolder, Band8threshold,Band8Dilation_Size)
                            LogList = LogList + LogListToAppend
                        elif Select_NDWI_or_BAND8_Masking == None:
                            ScriptOutput2List("Ignoring the use of NDWI-based or BAND8-based mask.", LogList)
                        
                        # Create CLOUD Mask using s2cloudless algorithm
                        if CloudMaskingS2cloudless == True:
                            ScriptOutput2List("Creating CLOUD Masks...", LogList)
                            LogListToAppend = CloudMasking_S2CloudLess_ROI_10m(ACOLITEoutputsFolder,ShortProductName, ProductMaskingFolder,S2CL_Threshold,S2CL_Average,S2CL_Dilation)
                            LogList = LogList + LogListToAppend
                        else:
                            ScriptOutput2List("Ignoring the use of cloud mask.", LogList)

                        # Create Final Mask based on WATER, NDWI and CLOUD masks depending on User Inputs
                        ScriptOutput2List("Creating FINAL Mask...", LogList)
                        LogListToAppend, MaskPath = CreateFinalMask(ProductMaskingFolder, UInFinalMask)
                        LogList = LogList + LogListToAppend
                        ScriptOutput2List("", LogList)
                        
                        # Apply final mask to all bands
                        ScriptOutput2List("Masking bands...", LogList)
                        # Create folder for each ACOLITE product inside folder of results
                        CreateBrandNewFolder(os.path.join(MaskedProductsFolder,ShortProductName))
                        for ACOLITEband in GenerateTifPaths(ACOLITEProductFile, ["B01","B02","B03","B04","B05","B06","B07","B08","B8A","B11","B12"]):
                            ACOLITEbandNameExt = os.path.basename(ACOLITEband)
                            # Initiate tif
                            MaskedBandPath = os.path.join(MaskedProductsFolder,ShortProductName, ACOLITEbandNameExt)
                            BandMasked = Driver.Create(MaskedBandPath, B2refSize[0], B2refSize[1], 1, gdal.GDT_Float32)
                            BandMasked.SetProjection(B2refRaster.GetProjectionRef())
                            BandMasked.SetGeoTransform(B2refRaster.GetGeoTransform())
                            # Open ACOLITE band to process
                            ACOLITErasterToProcess = gdal.Open(ACOLITEband)
                            ACOLITEbandToProcess = ACOLITErasterToProcess.GetRasterBand(1)
                            # Apply mask, also removes negative reflectances. Because of this the final bands might have gaps that are not in the final mask
                            MaskedBandData = ApplyMask(ACOLITEbandToProcess, MaskPath, FilterIgnoreValue=0, RemoveNegReflect=RemoveNegativeReflectances) 
                            MaskedBand = BandMasked.GetRasterBand(1)
                            MaskedBand.WriteArray(MaskedBandData)
                            BandMasked = None
                            # Close ACOLITE band
                            ACOLITErasterToProcess = None
                        # Close reference raster   
                        B2refRaster = None
                        ScriptOutput2List("Done.\n", LogList)

                        # Calculate and Save Indices (Must match indices used on ML model)
                        ScriptOutput2List("Calculating indices for " + ShortProductName, LogList)
                        CalculateAllIndexes(MaskedProductsFolder, ShortProductName)                     
                        ScriptOutput2List("Done.\n", LogList)          
                else:
                    ScriptOutput2List("Ignoring the middle steps: creation of masks, aplication of masks and calculation of indices.\n", LogList)

                # ### ML Classification: Supervised #########################################################################################################################################################################################
                if Classify == True:
                    # Check if product was excluded
                    if os.path.exists(os.path.join(S2L1CproductsFolder,SAFEFileName)):
                        TCtime = 0
                        # Start time of classification
                        Ctime0 = time.time()
                        ModelName = os.path.basename(ModelFolderPath)
                        ScriptOutput2List("Classifying " +  ShortProductName + " using " + ModelName + "...", LogList)

                        # Create brand new product folder to save SC files
                        ProductSCMapFolder = os.path.join(ResultsFolder, ShortProductName)
                        CreateBrandNewFolder(ProductSCMapFolder)

                        # Create dataframe to predict and produce a scene classification map
                        SelectBandsIndices = SelectFeaturessBasedOnModelName(ModelName)
                        ScriptOutput2List("Features: " +  str(SelectBandsIndices), LogList)
                        MaskedProductToProcess = os.path.join(MaskedProductsFolder, ShortProductName)
                        if ClassifyinJulia == False:
                            LogListToAppend = CreateSCmap(SelectBandsIndices, MaskedProductToProcess,ProductSCMapFolder, ModelFolderPath, ModelType, ClassProba,MLAlgorithm)
                        else:
                            LogListToAppend = CreateSCmap_Julia(SelectBandsIndices, MaskedProductToProcess,ProductSCMapFolder, ModelFolderPath,RF_model_jl)
                        LogList = LogList + LogListToAppend

                        # Finish time of classification
                        Ctimef = time.time()
                        #Duration of classification
                        ClassificationTime = int(Ctimef - Ctime0)
                        ScriptOutput2List("Classification Time: " + str(ClassificationTime) + " seconds.", LogList)
                        TCtime = TCtime + ClassificationTime
                        ScriptOutput2List("Done.\n", LogList)
                else:
                    ScriptOutput2List("Ignoring Classification.\n", LogList)
                
                #Delete intermediate files
                if DeleteIntermediateFiles == True:
                    Delete_Intermediate_Files(ACOLITEoutputsFolder,MaskedProductsFolder,ShortProductName)
                    ScriptOutput2List("Intermediate files are deleted from Acolite Products and Masked Output Folder.\n", LogList)
                # Delete original SAFE file from S2L1C product folder
                if DeleteOriginalProduct == True:
                    Delete_Original_Product(S2L1CproductsFolder,SAFEFileName)
                    ScriptOutput2List("Original Product is deleted from S2L1C Products Folder.\n", LogList)

                ScriptOutput2List("_________________________________________________________________________________________________________\n", LogList)
            except Exception as e:
                ScriptOutput2List("An error occured while processing the scene.\n", LogList)
                ScriptOutput2List(str(e) + "\n", LogList) 
                ScriptOutput2List("_________________________________________________________________________________________________________\n", LogList)      
        ScriptOutput2List("__________________________________________________End____________________________________________________\n", LogList)

    # Statistics about Products:
    NumberFoundProducts = len(ListS2L1CProducts_URLs)
    NumberExcludedProducts_OldFormat = len(ListofExcludedProducts_OldFormat)
    NumberExcludedProducts_NoData_SensingTime = len(ListofExcludedProducts_NoData_SensingTime)
    NumberProducts_COAH_LTA = len(Listof_COAH_LTA_Products)
    NumberProcessedProducts = NumberFoundProducts-(NumberExcludedProducts_OldFormat + NumberExcludedProducts_NoData_SensingTime + NumberProducts_COAH_LTA)
    
    # Products found in ROI for selected Sensing Period
    ScriptOutput2List("\nNumber of products FOUND for selected ROI and Sensing Period: " + str(NumberFoundProducts), LogList)
    # Products processed in ROI for selected Sensing Period
    ScriptOutput2List("Number of products PROCESSED for selected ROI and Sensing Period: " + str(NumberProcessedProducts), LogList)
    # Products excluded (old format)
    ExcludedProducts_OldFormat = '\n'.join(ListofExcludedProducts_OldFormat) + "\n"
    ScriptOutput2List("Number of products EXCLUDED (old format): " + str(NumberExcludedProducts_OldFormat), LogList)
    if len(ListofExcludedProducts_OldFormat) != 0:
        ScriptOutput2List(ExcludedProducts_OldFormat, LogList)  
    # Products excluded (ROI falls 100% on no data side of partial tile or scene have same sensing time)
    ExcludedProducts_NoData_SensingTime = '\n'.join(ListofExcludedProducts_NoData_SensingTime) + "\n"
    ScriptOutput2List("Number of products EXCLUDED (100% no data or same sensing time): " + str(NumberExcludedProducts_NoData_SensingTime), LogList)
    if len(ListofExcludedProducts_NoData_SensingTime) != 0:
        ScriptOutput2List(ExcludedProducts_NoData_SensingTime, LogList)
    # Products COAH LTA (product not available for retrieval from LTA)
    Products_COAH_LTA = '\n'.join(Listof_COAH_LTA_Products) + "\n"
    ScriptOutput2List("Number of products NOT AVAILABLE (COAH Long Term Archive): " + str(NumberProducts_COAH_LTA), LogList)
    if len(Listof_COAH_LTA_Products) != 0:
        ScriptOutput2List(Products_COAH_LTA, LogList)
    ScriptOutput2List("_________________________________________________________________________________________________________\n", LogList)
else:
    ScriptOutput2List("Ignoring the Processing of Products.\n", LogList)

### END ###################################################################################################################################################################################################################

# Finish time of processing
Ptimef = time.time()
# Duration of processing
ProcessingTime = int(Ptimef - Ptime0)

ScriptOutput2List("\nTotal Time: " + str(ProcessingTime) + " seconds.\n", LogList)

ScriptOutputs2LogFile(LogList, "LogFile")