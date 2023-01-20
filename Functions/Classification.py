#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
Functions used in ML Classification.

@author: AIR Centre
"""

### Import Libraries ###################################################################################################################
import glob
import os
import time
from osgeo import gdal
import numpy as np
import pandas as pd
import pickle as pkl
import xgboost as xgb
#from julia import Main as jl
from hummingbird.ml import load


#################################################################################################
def SelectFeaturessBasedOnModelName(ModelName):
    """
    This function selects the features (bands and indices) to use based on the model name.
    Input:  ModelName - Name of the model as string, must exist on dictionary.
    Output: Features - Bands and Indices in a tuple based on model name.
    """

    ModelAndFeatures = {'RF_Model_Example_MARIDA': ('B01', 'B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B8A', 'B11', 'B12') + ('NDVI', 'FAI', 'FDI', 'SI', 'NDWI', 'NRD', 'NDMI', 'BSI')}

    Features = ModelAndFeatures[ModelName]
    
    return Features

########################################################################################################################################
def CreateSCmap(SelectBandsIndices, FolderWithBandsAndIndices,OutputFolder, ModelFolderPath, ModelType="sk", OutputClassProba=False,MLAlgorithm="rf"):
    """
    This function creates a dataframe based on bands and indices to be predicted by the ML model. The prediction creates a Scene Classification map.
    The prediction can be performed on CPU or GPU.
    Map with the probability of predicted class can also be created.
    Input:  SelectBandsIndices - List of features (bands and indices). Must match the same features used in the training of the model.
            FolderWithBandsAndIndices - Folder path where the tif bands and indices are saved. The dataframe will be created based on that data. 
                                        The SC map will be saved on that same folder.
            ModelFolderPath - Path to folder where scikit trained model (.pkl) and pytorch conversion (.zip) are saved.
            ModelType - CPUpt for model converted to pytorch and processed on CPU.
                        GPUpt for model converted to pytorch and processed on GPU. Max size of model limited by GPU memory. 
                        Originalsk for original model created with scikit, other inputs will be consider as Originalsk.
            OutputClassProba - Outputs a .tif file with class probability for each pixel predicted by the model
    Output: LogList - Function's log outputs. List of strings. 
            Scene Classification map as tif.
            Class probability map as tif (optional).
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
    # Classes probability
    if OutputClassProba == True:
        DFofProbaResultsStruct = pd.DataFrame(0, index=range(0, len(DFtoPredict.index)), columns=['Prob'])
    
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
        # Classes probability
        if OutputClassProba == True:
            ProbaResultsFlat = np.array(DFofProbaResultsStruct).flatten()
            ProbaResultsReshape = ProbaResultsFlat.reshape(RasterDataShape)
    else:
        OutputLog = "Performing classification for dataframe with no NaNs of shape " + str(DFtoPredictWithoutNaN.shape) + "."
        LogList.append(OutputLog)
        print(OutputLog)

        # Load ML model depending on Model Type
        if ModelType == "CPUpt":
            ModelPathConv = glob.glob(os.path.join(ModelFolderPath, "*.zip"))[0]
            MLmodel = load(ModelPathConv)
        elif ModelType == "GPUpt":
            ModelPathConv = glob.glob(os.path.join(ModelFolderPath, "*.zip"))[0]
            MLmodel = load(ModelPathConv)
            MLmodel.to('cuda')
        else:
            ModelPathOrig = glob.glob(os.path.join(ModelFolderPath, "*.pkl"))[0]
            MLmodel = pkl.load(open(ModelPathOrig, 'rb'))


        # Predict using model (class probability is optional)
        TCtime = 0
        # Start time of prediction
        Ctime0 = time.time()
        if MLAlgorithm== "xgb":
            ClassiResults_prov = MLmodel.predict(DFtoPredictWithoutNaN)
            ClassiResults= ClassiResults_prov+1
        else:
            ClassiResults = MLmodel.predict(DFtoPredictWithoutNaN)
        # Finish time of predition
        Ctimef = time.time()
        #Duration of prediction
        ClassificationTime = int(Ctimef - Ctime0)
        OutputLog = "Prediction Time: " + str(ClassificationTime) + " seconds."
        LogList.append(OutputLog)
        print(OutputLog)
        # Classes probability
        if OutputClassProba == True:
            ProbaResults_All = MLmodel.predict_proba(DFtoPredictWithoutNaN)
            ProbaResults = np.max(ProbaResults_All)
                
        # Index results, construct final dataframe and reshape
        ClassiResultsIndexed = pd.DataFrame(ClassiResults, index=DFtoPredictWithoutNaN.index, columns=['ClassNum'])
        DFofClassiResults = ClassiResultsIndexed.combine_first(DFofClassiResultsStruct)
        ClassiResultsFlat = np.array(DFofClassiResults).flatten()
        ClassiResultsReshape = ClassiResultsFlat.reshape(RasterDataShape)
        if OutputClassProba == True:
            ProbaResultsIndexed = pd.DataFrame(ProbaResults, index=DFtoPredictWithoutNaN.index, columns=['Prob'])
            DFofProbaResults = ProbaResultsIndexed.combine_first(DFofProbaResultsStruct)
            ProbaResultsFlat = np.array(DFofProbaResults).flatten()
            ProbaResultsReshape = ProbaResultsFlat.reshape(RasterDataShape)
        
    # Initiate raster and save scene classification results to folder
    Driver = gdal.GetDriverByName("GTiff")
    SCraster = Driver.Create(os.path.join(OutputFolder,"SCmap.tif"), Raster.RasterXSize, Raster.RasterYSize, 1, gdal.GDT_Byte)
    SCraster.SetProjection(Raster.GetProjectionRef())
    SCraster.SetGeoTransform(Raster.GetGeoTransform())
    SCrasterBand = SCraster.GetRasterBand(1)
    SCrasterBand.WriteArray(ClassiResultsReshape)
    SCraster = None
    
    # Classes probability
    if OutputClassProba == True:
        # Initiate raster and save probabilities results to folder
        Driver = gdal.GetDriverByName("GTiff")
        PROBAraster = Driver.Create(os.path.join(OutputFolder,"PROBAmap.tif"), Raster.RasterXSize, Raster.RasterYSize, 1, gdal.GDT_Float32)
        PROBAraster.SetProjection(Raster.GetProjectionRef())
        PROBAraster.SetGeoTransform(Raster.GetGeoTransform())
        PROBArasterBand = PROBAraster.GetRasterBand(1)
        PROBArasterBand.WriteArray(ProbaResultsReshape)
        PROBAraster = None

    return LogList

########################################################################################################################################

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
        OutputLog = "Prediction Time: " + str(round(dt)) + " seconds."
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







