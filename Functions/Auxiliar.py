#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
Auxiliar Functions.

@author: AIR Centre
"""

### Import Libraries ############################################################################
import os
import shutil
from datetime import datetime, timedelta

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
def Delete_Intermediate_Files(ACOLITEoutputsFolder,ResultsFolder,ShortProductName):
    """
    This function deletes intermediate files in the ACOLITE Output Folder:
    (rayleigh corrected bands,surface reflectance bands, top of atmosphere bands, stacked bands)
    Input:  Acolite output folder path - List of paths to the TIF files.
    Output: Deleting of listed files.
    """
    # Check if product folder exists
    if os.path.exists(os.path.join(ACOLITEoutputsFolder,ShortProductName)):
        ListNameofFilesToDelete_rhos = ['rhos_B01','rhos_B02','rhos_B03','rhos_B04','rhos_B05','rhos_B06','rhos_B07','rhos_B08','rhos_B8A','rhos_B11','rhos_B12']
        for NameFiletoDelete in ListNameofFilesToDelete_rhos:
            FileToDelete = os.path.join(ACOLITEoutputsFolder,ShortProductName, 'Surface_Reflectance_Bands', NameFiletoDelete  + '.tif')
            if os.path.exists(FileToDelete):
                os.remove(FileToDelete)
        ListNameofFilesToDelete_rhot = ['rhot_B01','rhot_B02','rhot_B03','rhot_B04','rhot_B05','rhot_B06','rhot_B07','rhot_B08','rhot_B8A','rhot_B09','rhot_B10','rhot_B11','rhot_B12']
        for NameFiletoDelete in ListNameofFilesToDelete_rhot:
            FileToDelete = os.path.join(ACOLITEoutputsFolder,ShortProductName, 'Top_Atmosphere_Bands', NameFiletoDelete  + '.tif')
            if os.path.exists(FileToDelete):
                os.remove(FileToDelete)
        ListNameofFilesToDelete_rhorc = ['B01','B02','B03','B04','B05','B06','B07','B08','B8A','B11','B12','BSI','FAI','FDI','NDMI','NDVI','NDWI','NRD','SI']
        for NameFiletoDelete in ListNameofFilesToDelete_rhorc:
            FileToDelete = os.path.join(ACOLITEoutputsFolder,ShortProductName, NameFiletoDelete  + '.tif')
            if os.path.exists(FileToDelete):
                os.remove(FileToDelete)
        FileToDelete = os.path.join(ACOLITEoutputsFolder,ShortProductName, ShortProductName + '_StackedBands.tif')
        if os.path.exists(FileToDelete):
            os.remove(FileToDelete)
        ListNameofFilesToDelete_results = ['B01','B02','B03','B04','B05','B06','B07','B08','B8A','B11','B12','BSI','FAI','FDI','NDMI','NDVI','NDWI','NRD','SI']
        for NameFiletoDelete in ListNameofFilesToDelete_results:
            FileToDelete = os.path.join(ResultsFolder,ShortProductName, NameFiletoDelete  + '.tif')
            if os.path.exists(FileToDelete):
                os.remove(FileToDelete)

#################################################################################################
def Delete_Original_Product(S2L1CproductsFolder,SAFEFileName):
    """
    This function deletes original SAFE product in the S2L1C Product Folder:
    Input:  S2L1C output folder path - path to the SAFE file.
    Output: Deleting of SAFE file.
    """
    # Check if product exists
    if os.path.exists(os.path.join(S2L1CproductsFolder,SAFEFileName)):
        ProductToDelete=os.path.join(S2L1CproductsFolder,SAFEFileName)
        shutil.rmtree(ProductToDelete)
        