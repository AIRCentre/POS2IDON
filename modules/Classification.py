#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
Functions used in ML Classification.

@author: AIR Centre
"""

### Import Libraries ###################################################################################################
import glob
import os
import numpy as np
import pandas as pd
import pickle as pkl
from osgeo import gdal
import rasterio as rio
import xgboost as xgb
from hummingbird.ml import load
#import cv2 # Solves problem of segmentation fault when importing torch?
import torch
import torchvision.transforms as transforms
import time
#from julia import Main as jl

### unet.py ############################################################################################################
from modules.unet import UNet
from modules.PreStart import ScriptOutput2List
from modules.Auxiliar import CreateBrandNewFolder

########################################################################################################################
def load_ml_model(model_folder, classification_options):
    """
    Loads a model depending on model_type from classification_options.
    """
    # RF or XGB
    if (classification_options["model_type"] == "CPUpt") and (classification_options["ml_algorithm"] != "unet"):
        model_path = glob.glob(os.path.join(model_folder, "*.zip"))[0]
        model = load(model_path)
        device = None
    
    elif (classification_options["model_type"] == "GPUpt") and (classification_options["ml_algorithm"] != "unet"): 
        model_path = glob.glob(os.path.join(model_folder, "*.zip"))[0]
        model = load(model_path)
        model.to('cuda')
        device = None
    
    elif (classification_options["model_type"] == "sk") and (classification_options["ml_algorithm"] != "unet"): 
        model_path = glob.glob(os.path.join(model_folder, "*.pkl"))[0]
        model = pkl.load(open(model_path, 'rb'))
        device = None
    
    else: # UNET
        # Use gpu or cpu
        if torch.cuda.is_available():
            device = torch.device("cuda")
        else:
            device = torch.device("cpu")
        # Model structure
        model = UNet(len(classification_options["features"]), classification_options["n_classes"], classification_options["n_hchannels"])
        model.to(device)
        # Load model from specific epoch to continue the training or start the evaluation
        model_path = glob.glob(os.path.join(model_folder, "*.pth"))[0]
        checkpoint = torch.load(model_path, map_location=device)
        model.load_state_dict(checkpoint)
        del checkpoint  # dereference
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        model.eval()

    return model, device

########################################################################################################################
def convert_stack_rfxgb(image, classification_options):
    """
    This function only reads the features of interest from a stack TIF file.
    Then it converts to dataframe (RF and XGB) or a short version of the stack raster (UNET).
    ATTENTION: If you decide to include more features than the default 'all_features', you 
               will need to change the dictionary.
    """
    # Read stack
    stack_raster = gdal.Open(image)

    # Select features of interest from the stack
    all_features = {'B01':1, 'B02':2, 'B03':3, 'B04':4, 'B05':5, 'B06':6, 'B07':7, 'B08':8, 'B8A':9, 'B11':10, 
                    'B12':11, 'NDVI':12, 'FAI':13, 'FDI':14, 'SI':15, 'NDWI':16, 'NRD':17, 'NDMI':18, 'BSI':19}
    features_n = [all_features[i] for i in classification_options["features"]]

        
    # Create dataframe with only the data from the features of interest
    # Init
    init_stack_data = stack_raster.GetRasterBand(features_n[0]).ReadAsArray()
    # Reshape as single column
    stack_data = init_stack_data.reshape(-1,1)

    for feature_n in features_n[1:]:
        # Get data
        feature_stack_data = stack_raster.GetRasterBand(feature_n).ReadAsArray()
        feature_stack_reshaped = feature_stack_data.reshape(-1,1)
        stack_data = np.concatenate([stack_data, feature_stack_reshaped], axis=1)

    # Shape to use in reshape
    stack_data_shape = init_stack_data.shape
    # Global dataframe to predict
    global_predict_df = pd.DataFrame(stack_data, columns=classification_options["features"])

    # Dataframe to predict, without NaNs
    no_nans_predict_df = global_predict_df.dropna(axis=0, how='any')

    return stack_raster, stack_data_shape, global_predict_df, no_nans_predict_df

########################################################################################################################
def save_maps(output_folder, image_name, img, predict_results_reshape, probability_results_reshape):
    """
    This function saves the scene classification and probability maps.
    """
    sc_output_folder = os.path.join(output_folder, "sc_maps")
    # Initiate raster and save scene classification results to folder
    driver = gdal.GetDriverByName("GTiff")
    sc_raster = driver.Create(os.path.join(sc_output_folder, image_name+"-scmap.tif"), img.RasterXSize, img.RasterYSize, 1, gdal.GDT_Byte)
    sc_raster.SetProjection(img.GetProjectionRef())
    sc_raster.SetGeoTransform(img.GetGeoTransform())
    sc_raster_band = sc_raster.GetRasterBand(1)
    sc_raster_band.WriteArray(predict_results_reshape)
    sc_raster = None

    # Classes probability
    if probability_results_reshape is not None:
        proba_output_folder = os.path.join(output_folder, "proba_maps")
        # Initiate raster and save probabilities results to folder
        driver = gdal.GetDriverByName("GTiff")
        probability_raster = driver.Create(os.path.join(proba_output_folder, image_name+"-probamap.tif"), img.RasterXSize, img.RasterYSize, 1, gdal.GDT_Float32)
        probability_raster.SetProjection(img.GetProjectionRef())
        probability_raster.SetGeoTransform(img.GetGeoTransform())
        probability_raster_band = probability_raster.GetRasterBand(1)
        probability_raster_band.WriteArray(probability_results_reshape)
        probability_raster = None

########################################################################################################################
def rfxgb_prediction(model, output_folder, image_name, img, img_shape, global_predict_df, no_nans_predict_df, ignore_log, classification_options):
    """
    This function uses RF or XGBoost to predict one or more images.
    """
    log_list = []

    # Structure of zero dataframe to store results
    # Classification
    predict_results_struct_df = pd.DataFrame(0, index=range(0, len(global_predict_df.index)), columns=['ClassNum'])
    # Classes probability
    if classification_options["classification_probabilities"] == True:
        probability_results_struct_df = pd.DataFrame(0, index=range(0, len(global_predict_df.index)), columns=['Prob'])

    # If dataframe to predict without NaNs is empty, then the final classification is only 0 (the same for probabilities).
    # A calculation between available data for prediction (without NaNs) and total data can be done here to only consider a percentage of more than 80% 
    if len(no_nans_predict_df.index) == 0:
        if ignore_log == False:
            ScriptOutput2List("Classification ignored, no dataframe without NaNs to predict.", log_list)
        predict_results_flat = np.array(predict_results_struct_df).flatten()
        predict_results_reshape = predict_results_flat.reshape(img_shape)
        # Classes probability
        if classification_options["classification_probabilities"] == True:
            probability_results_flat = np.array(probability_results_struct_df).flatten()
            probability_results_reshape = probability_results_flat.reshape(img_shape)
        else:
            probability_results_reshape = None

    else:
        if ignore_log == False:
            ScriptOutput2List("Dataframe with no NaNs of shape " + str(no_nans_predict_df.shape) + ".", log_list)
        # Prediction
        if classification_options["ml_algorithm"] == "xgb":
            predict_results_0 = model.predict(no_nans_predict_df)
            predict_results = predict_results_0 + 1
        else:
            predict_results = model.predict(no_nans_predict_df)

        if classification_options["classification_probabilities"] == True:
            probability_results_all = model.predict_proba(no_nans_predict_df)
            probability_results = np.max(probability_results_all)
         
        # Index results, construct final dataframe and reshape
        predict_results_indexed = pd.DataFrame(predict_results, index=no_nans_predict_df.index, columns=['ClassNum'])
        predict_results_df = predict_results_indexed.combine_first(predict_results_struct_df)
        predict_results_flat = np.array(predict_results_df).flatten()
        predict_results_reshape = predict_results_flat.reshape(img_shape)
        if classification_options["classification_probabilities"] == True:
            probability_results_indexed = pd.DataFrame(probability_results, index=no_nans_predict_df.index, columns=['Prob'])
            probability_results_df = probability_results_indexed.combine_first(probability_results_struct_df)
            probability_results_flat = np.array(probability_results_df).flatten()
            probability_results_reshape = probability_results_flat.reshape(img_shape)
        else:
            probability_results_reshape = None

    # Save maps
    save_maps(output_folder, image_name, img, predict_results_reshape, probability_results_reshape)

    return log_list
        
########################################################################################################################
def convert_stack_unet(image, classification_options):
    """
    This function only reads the features of interest from a stack TIF file.
    Then it converts to a short version of the stack raster (UNET).
    ATTENTION: If you decide to include more features than the default 'all_features', you 
               will need to change the dictionary.
    """
    # Select features of interest from the stack
    all_features = {'B01':1, 'B02':2, 'B03':3, 'B04':4, 'B05':5, 'B06':6, 'B07':7, 'B08':8, 'B8A':9, 'B11':10, 
                    'B12':11, 'NDVI':12, 'FAI':13, 'FDI':14, 'SI':15, 'NDWI':16, 'NRD':17, 'NDMI':18, 'BSI':19}
    features_n = [all_features[i] for i in classification_options["features"]]

    # Read image
    with rio.open(image, mode ='r') as src:
        tags = src.tags().copy()
        meta = src.meta
        img = src.read(features_n)
        img = np.moveaxis(img, (0, 1, 2), (2, 0, 1))
        dtype = src.read(1).dtype

    return img, meta, tags, dtype

########################################################################################################################
def unet_prediction(device, model, output_folder, image_name, img, meta, tags, dtype, classification_options):
    """
    This function uses Unet to predict one or more images.
    """
    # sc_maps folder
    scmaps_folder = os.path.join(output_folder, "sc_maps")
    # Output file path
    scmap_path = os.path.join(scmaps_folder, image_name+"_unet-scmap.tif")
    
    # proba_maps folder
    if classification_options["classification_probabilities"] == True:
        probamaps_folder = os.path.join(output_folder, "proba_maps") 
        probamap_path = os.path.join(probamaps_folder, image_name+"_unet-probamap.tif")
    
    impute_nan = np.tile(classification_options["features_mean"], (256,256,1))
    transform_test = transforms.Compose([transforms.ToTensor()])
    standardization = transforms.Normalize(classification_options["features_mean"], classification_options["features_std"])

    # Update meta to reflect the number of layers
    meta.update(count = 1)

    # Preprocessing before prediction
    nan_mask = np.isnan(img)
    img[nan_mask] = impute_nan[nan_mask]
    img = transform_test(img)
    img = standardization(img) 

    # Image to Cuda if exist
    img = img.to(device)

    # Predictions
    logits = model(img.unsqueeze(0))
    probs = torch.nn.functional.softmax(logits.detach(), dim=1).cpu().numpy()
    if classification_options["classification_probabilities"] == True:
        probs_i = probs.max(axis=1).squeeze()
        probs = probs.argmax(1).squeeze()+1
        # Write TIFs
        with rio.open(scmap_path, 'w', **meta) as dst:
            dst.write_band(1, probs.astype(dtype).copy())
            dst.update_tags(**tags)
        with rio.open(probamap_path, 'w', **meta) as dst:
            dst.write_band(1, probs_i.copy())
            dst.update_tags(**tags)
    else:
        probs = probs.argmax(1).squeeze()+1
        # Write TIF
        with rio.open(scmap_path, 'w', **meta) as dst:
            dst.write_band(1, probs.astype(dtype).copy())
            dst.update_tags(**tags)

########################################################################################################################
def create_sc_proba_maps(input_folder, output_folder, classification_options):
    """
    This function uses a Machine Learning Algorithm (Random Forest, XGBoost or Unet) to predict one image or several
    patches. It creates scene classification and probability maps.
    Input: input_folder - Path to the folder where TIF (image) or TIFs (patches) with all features stacked (bands and indices) are located. String.
           output_folder - Path to the folder where the folders with scene classification (and probability) maps will be saved. String.
           classification_options - Dictionary with following information:
                                    "model_path" - Path to the folder where the model file is saved.
                                    "model_type" - 'CPUpt' for model converted to pytorch and processed on CPU.
                                                   'GPUpt' for model converted to pytorch and processed on GPU. Max size of model limited by GPU memory. 
                                                   'sk' for model created with scikit. Other inputs will be consider as None.
                                                    Only valid for RF and XGB. None for UNET.
                                    "n_hchannels" - UNET Number of hidden channels. None for RF and XGB.
                                    "features" - Tuple of features.
                                    "features_mean" - UNET features mean values. None for RF and XGB.
                                    "features_std" - UNET features standard deviation values. None for RF and XGB.
                                    "n_classes" - Number of classes.
                                    "classification_probabilities" - Outputs class probability for each pixel predicted by the model. Bool.
                                    "ml_algorithm" - 'rf' for Random Forest.
                                                     'xgb' for XGBoost.
                                                     'unet' for Unet.
    Output: log_list - Function's log outputs. List of strings. 
            Scene Classification maps as TIF.
            Class probability maps as TIF (optional).
    """
    ptime_0 = time.time()
    log_list = []

    # Create folders to save maps
    # Create sc_maps folder
    CreateBrandNewFolder(os.path.join(output_folder, "sc_maps"))   
    # Create proba_maps folder
    CreateBrandNewFolder(os.path.join(output_folder, "proba_maps")) 

    # Load model, must be done outside loop to save time
    ScriptOutput2List("Loading ML model...", log_list)
    model, device = load_ml_model(classification_options["model_path"], classification_options)
    ScriptOutput2List("Model loaded.\n", log_list)

    # Check folder TIFs
    tifs_list = glob.glob(os.path.join(input_folder, "*.tif"))
    ScriptOutput2List("Classification of " + str(len(tifs_list)) + " images.\n", log_list)
    if len(tifs_list) > 0:
        ignore_log = True

    # Random Forest
    if classification_options["ml_algorithm"] == "rf":
        ScriptOutput2List("Performing classification with Random Forest...", log_list)
        # Cycle each TIF
        for image in tifs_list:
            image_name = os.path.basename(image)[:-4]+"_rf"
            # Convert full stack to desired DF
            img, img_data_shape, global_predict_df, no_nans_predict_df = convert_stack_rfxgb(image, classification_options)
            # Prepare data even more and prediction
            log_list0 = rfxgb_prediction(model, output_folder, image_name, img, img_data_shape, global_predict_df, no_nans_predict_df, ignore_log, classification_options)
            log_list = log_list + log_list0
        
    # XGBoost
    elif classification_options["ml_algorithm"] == "xgb":
        ScriptOutput2List("Performing classification with XGBoost...", log_list)
        # Cycle each TIF
        for image in tifs_list:
            image_name = os.path.basename(image)[:-4]+"_xgb"
            # Convert full stack to desired DF
            img, img_data_shape, global_predict_df, no_nans_predict_df = convert_stack_rfxgb(image, classification_options)
            # Prepare data even more and prediction
            log_list0 = rfxgb_prediction(model, output_folder, image_name, img, img_data_shape, global_predict_df, no_nans_predict_df, ignore_log, classification_options)
            log_list = log_list + log_list0

    # Unet
    elif classification_options["ml_algorithm"] == "unet":
        ScriptOutput2List("Performing classification with Unet...", log_list)
        # Cycle each TIF
        for image in tifs_list:
            image_name = os.path.basename(image)[:-4]
            # Prepare data to predict
            img, meta, tags, dtype = convert_stack_unet(image, classification_options)
            # Prediction
            unet_prediction(device, model, output_folder, image_name, img, meta, tags, dtype, classification_options)
    
    # Other
    else:
        ScriptOutput2List("Machine Learning algorithm option not defined.", log_list)

    ptime_f = time.time()
    ptime = int(ptime_f - ptime_0)
    ScriptOutput2List("Done. Classification time with all steps: " + str(ptime) + " seconds.\n", log_list)

    return log_list  

########################################################################################################################################
# CHECK THIS
def CreateSCmap_Julia(SelectBandsIndices, FolderWithBandsAndIndices,OutputFolder, ModelFolderPath,RF_model_jl):
    """
    This function creates a dataframe based on bands and indices to be predicted with Julia by the ML model. The prediction creates a Scene Classification map.
    The prediction can be performed on CPU or GPU.
    Map with the probability of predicted class can also be created.
    Input:  SelectBandsIndices - List of features (bands and indices). Must match the same features used in the training of the model.
            FolderWithBandsAndIndices - Folder path where the tif bands and indices are saved. The dataframe will be created based on that data. 
                                        The SC map will be saved on that same folder.
            ModelFolderPath - Path to folder where julia trained model (.jl2d) is saved.
            Julia Model to be used - String (inside function)
            OutputClassProba - Outputs a .tif file with class probability for each pixel predicted by the model
    Output: LogList - Function's log outputs. List of strings. 
            Scene Classification map as tif.
    """
    LogList = []

    # Import bands and indices paths, stack them into dataframe
    # Init
    # File path
    FileName = SelectBandsIndices[0]+'.tif'
    FilePath = glob.glob(os.path.join(FolderWithBandsAndIndices, FileName))[0]
    # Get data
    Raster = gdal.Open(FilePath)
    RasterData = Raster.GetRasterBand(1).ReadAsArray()
    # Reshape as single column
    StackedRasterData = RasterData.reshape(-1,1)

    for FileBasename in SelectBandsIndices[1:]:
        # File path
        FileName = FileBasename+'.tif'
        FilePath = glob.glob(os.path.join(FolderWithBandsAndIndices, FileName))[0]
        # Get data
        Raster = gdal.Open(FilePath)
        RasterData = Raster.GetRasterBand(1).ReadAsArray()
        RasterDataReshaped = RasterData.reshape(-1,1)
        StackedRasterData = np.concatenate([StackedRasterData, RasterDataReshaped], axis=1)

    # Shape to use in reshape
    RasterDataShape = RasterData.shape
    # Global dataframe to predict
    DFtoPredict = pd.DataFrame(StackedRasterData, columns=SelectBandsIndices)
    
    # Structure of zero dataframe to store results
    # Classification
    DFofClassiResultsStruct = pd.DataFrame(0, index=range(0, len(DFtoPredict.index)), columns=['ClassNum'])
    
    # Dataframe to predict, without NaNs
    DFtoPredictWithoutNaN = DFtoPredict.dropna(axis=0, how='any')

    # If dataframe to predict without NaNs is empty, then the final classification  is only 0 (the same for probabilities).
    # A calculation between available data for prediction (without NaNs) and total data can be done here to only consider a percentage of more than 80% 
    if len(DFtoPredictWithoutNaN.index) == 0:
        OutputLog = "Classification ignored, no dataframe without NaNs to predict."
        LogList.append(OutputLog)
        print(OutputLog)
        ClassiResultsFlat = np.array(DFofClassiResultsStruct).flatten()
        ClassiResultsReshape = ClassiResultsFlat.reshape(RasterDataShape)
    else:
        OutputLog = "Performing classification for dataframe with no NaNs of shape " + str(DFtoPredictWithoutNaN.shape) + "."
        LogList.append(OutputLog)
        print(OutputLog)
        
        # Call Julia script where the function is included
        jl.include("Functions/Classification.jl")
        # Call Julia Function
        ClassiResults,dt = jl.Classification_Julia(ModelFolderPath,DFtoPredictWithoutNaN,RF_model_jl)
        OutputLog = "Classification Time: " + str(round(dt)) + " seconds."
        LogList.append(OutputLog)
        print(OutputLog)
        # Index results, construct final dataframe and reshape
        ClassiResultsIndexed = pd.DataFrame(ClassiResults, index=DFtoPredictWithoutNaN.index, columns=['ClassNum'])
        DFofClassiResults = ClassiResultsIndexed.combine_first(DFofClassiResultsStruct)
        ClassiResultsFlat = np.array(DFofClassiResults).flatten()
        ClassiResultsReshape = ClassiResultsFlat.reshape(RasterDataShape)
        
    # Initiate raster and save scene classification results to folder
    Driver = gdal.GetDriverByName("GTiff")
    SCraster = Driver.Create(os.path.join(OutputFolder,"SCmap.tif"), Raster.RasterXSize, Raster.RasterYSize, 1, gdal.GDT_Byte)
    SCraster.SetProjection(Raster.GetProjectionRef())
    SCraster.SetGeoTransform(Raster.GetGeoTransform())
    SCrasterBand = SCraster.GetRasterBand(1)
    SCrasterBand.WriteArray(ClassiResultsReshape)
    SCraster = None

    return LogList

########################################################################################################################################






