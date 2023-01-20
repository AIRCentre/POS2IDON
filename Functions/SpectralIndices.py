#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
Functions to calculate spectral indices.

@author: AIR Centre
"""

### Import Libraries ###################################################################################################################
from osgeo import gdal
import numpy as np
import os

### Import Defined Functions ###########################################################################################################
from Functions.Auxiliar import *

########################################################################################################################################
def CalculateNormalizedIndexTif(BandPaths, PathAndTifName):
    """
    This function calculates a normalized index using two bands and saves as tif file.
    Input: BandPaths - List with two band paths [BandPath1, BandPath2] to use in the 
                       calculation [(BandData1-BandData2)/(BandData1+BandData2)]. The 
                       first band will be used as reference for the new raster.  
           PathAndTifName - Path where the tif file will be saved (includes name of file).
    Output: Normalized index tif file. 
    """
    
    # Extract data from bands
    Band1Raster = gdal.Open(BandPaths[0])
    Band1Data = Band1Raster.GetRasterBand(1).ReadAsArray()
    Band2Raster = gdal.Open(BandPaths[1])
    Band2Data = Band2Raster.GetRasterBand(1).ReadAsArray()
    
    # Calculation. Allow division by zero
    np.seterr(divide="ignore", invalid="ignore")
    NIdata = (Band1Data-Band2Data)/(Band1Data+Band2Data)
    
    # Initiate raster and save to folder
    Driver = gdal.GetDriverByName("GTiff")
    NIraster = Driver.Create(PathAndTifName, Band1Raster.RasterXSize, Band1Raster.RasterYSize, 1, gdal.GDT_Float32)
    NIraster.SetProjection(Band1Raster.GetProjectionRef())
    NIraster.SetGeoTransform(Band1Raster.GetGeoTransform())
    
    NIrasterBand = NIraster.GetRasterBand(1)
    NIrasterBand.WriteArray(NIdata)
    NIraster = None
    # Close opened bands
    Band1Raster = None
    Band2Raster = None

########################################################################################################################################
def CalculateFAIorFDItif(B4B6B8B11Paths, S2platform, PathAndTifName, Index):
    """
    This function calculates the Floating Algae Index or Floating Debris Index and 
    saves to a folder.
    Input: B4B6B8B11Paths - List with band paths [B4path, B6path, B8path, B11path] to use
                            in the calculation of FAI or FDI.
           S2platform - String with S2A or S2B platforms.                 
           PathAndTifName - Path where the tif file will be saved (includes name of file).
           Index - String with FAI or FDI.
    Output: FAI or FDI tif file.
    """

    # Select central wavelength according to Sentinel-2 platform (S2-A or -B)
    if S2platform == "S2A":
        wlB04 = 664.6
        wlB06 = 740.5
        wlB08 = 832.8
        wlB11 = 1613.7
    else:
        wlB04 = 664.9
        wlB06 = 739.1
        wlB08 = 832.9
        wlB11 = 1610.4
    
    # Extract data from bands
    B04Raster = gdal.Open(B4B6B8B11Paths[0])
    B04Data = B04Raster.GetRasterBand(1).ReadAsArray()

    B06Raster = gdal.Open(B4B6B8B11Paths[1])
    B06Data = B06Raster.GetRasterBand(1).ReadAsArray()
   
    B08Raster = gdal.Open(B4B6B8B11Paths[2])
    B08Data = B08Raster.GetRasterBand(1).ReadAsArray()
    
    B11Raster = gdal.Open(B4B6B8B11Paths[3])
    B11Data = B11Raster.GetRasterBand(1).ReadAsArray()
        
    # Calculate FAI or FDI
    if Index == "FAI":
        IndexData = B08Data - (B04Data + (B11Data-B04Data)*((wlB08-wlB04)/(wlB11-wlB04)))
    else:
        IndexData = B08Data - (B06Data + (B11Data-B06Data)*((wlB08-wlB06)/(wlB11-wlB06))*10)
    
    # Save Index
    Driver = gdal.GetDriverByName("GTiff")
    IndexRaster = Driver.Create(PathAndTifName, B04Raster.RasterXSize, B04Raster.RasterYSize, 1, gdal.GDT_Float32)
    IndexRaster.SetProjection(B04Raster.GetProjectionRef())
    IndexRaster.SetGeoTransform(B04Raster.GetGeoTransform()) 
    
    IndexRasterBand = IndexRaster.GetRasterBand(1)
    IndexRasterBand.WriteArray(IndexData)
    IndexRaster = None
    # Close opened bands
    B04Raster = None
    B06Raster = None
    B08Raster = None
    B11Raster = None

########################################################################################################################################  
def CalculateSITif(BandPaths, PathAndTifName):
    """
    This function calculates shadow index using three bands and saves as tif file.
    Input: BandPaths - List with three band paths [Band2Path, Band3Path, Band4Path] to use in the 
                       calculation. The first band will be used as reference for the new raster.  
           PathAndTifName - Path where the tif file will be saved (includes name of file).
    Output: SI tif file. 
    """
    
    # Extract data from bands
    Band2Raster = gdal.Open(BandPaths[0])
    Band2Data = Band2Raster.GetRasterBand(1).ReadAsArray()
    Band3Raster = gdal.Open(BandPaths[1])
    Band3Data = Band3Raster.GetRasterBand(1).ReadAsArray()
    Band4Raster = gdal.Open(BandPaths[2])
    Band4Data = Band4Raster.GetRasterBand(1).ReadAsArray()
    
    # Calculation. Allow division by zero
    np.seterr(divide="ignore", invalid="ignore")
    SIdata = ((1-Band2Data)*(1-Band3Data)*(1-Band4Data))**(1/3)
    
    # Initiate raster and save to folder
    Driver = gdal.GetDriverByName("GTiff")
    SIraster = Driver.Create(PathAndTifName, Band2Raster.RasterXSize, Band2Raster.RasterYSize, 1, gdal.GDT_Float32)
    SIraster.SetProjection(Band2Raster.GetProjectionRef())
    SIraster.SetGeoTransform(Band2Raster.GetGeoTransform())
    
    SIrasterBand = SIraster.GetRasterBand(1)
    SIrasterBand.WriteArray(SIdata)
    SIraster = None

    # Close opened bands
    Band2Raster = None
    Band3Raster = None
    Band4Raster = None

########################################################################################################################################
def CalculateNRDTif(BandPaths, PathAndTifName):
    """
    This function calculates NRD using two bands and saves as tif file.
    Input: BandPaths - List with two band paths [Band8Path, Band4Path] to use in the 
                       calculation. The first band will be used as reference for the new raster.  
           PathAndTifName - Path where the tif file will be saved (includes name of file).
    Output: NRD tif file. 
    """
    
    # Extract data from bands
    Band8Raster = gdal.Open(BandPaths[0])
    Band8Data = Band8Raster.GetRasterBand(1).ReadAsArray()
    Band4Raster = gdal.Open(BandPaths[1])
    Band4Data = Band4Raster.GetRasterBand(1).ReadAsArray()
    
    # Calculation. Allow division by zero
    np.seterr(divide="ignore", invalid="ignore")
    NRDdata = Band8Data - Band4Data
    
    # Initiate raster and save to folder
    Driver = gdal.GetDriverByName("GTiff")
    NRDraster = Driver.Create(PathAndTifName, Band8Raster.RasterXSize, Band8Raster.RasterYSize, 1, gdal.GDT_Float32)
    NRDraster.SetProjection(Band8Raster.GetProjectionRef())
    NRDraster.SetGeoTransform(Band8Raster.GetGeoTransform())
    
    NRDrasterBand = NRDraster.GetRasterBand(1)
    NRDrasterBand.WriteArray(NRDdata)
    NRDraster = None

    # Close opened bands
    Band8Raster = None
    Band4Raster = None

########################################################################################################################################
def CalculateBSITif(BandPaths, PathAndTifName):
    """
    This function calculates bare soil index using four bands and saves as tif file.
    Input: BandPaths - List with four band paths [Band2Path, Band4Path, Band8Path, Band11Path] to use in the 
                       calculation. The first band will be used as reference for the new raster.  
           PathAndTifName - Path where the tif file will be saved (includes name of file).
    Output: BSI tif file. 
    """
    
    # Extract data from bands
    Band2Raster = gdal.Open(BandPaths[0])
    Band2Data = Band2Raster.GetRasterBand(1).ReadAsArray()
    Band4Raster = gdal.Open(BandPaths[1])
    Band4Data = Band4Raster.GetRasterBand(1).ReadAsArray()
    Band8Raster = gdal.Open(BandPaths[2])
    Band8Data = Band8Raster.GetRasterBand(1).ReadAsArray()
    Band11Raster = gdal.Open(BandPaths[3])
    Band11Data = Band11Raster.GetRasterBand(1).ReadAsArray()
    
    # Calculation. Allow division by zero
    np.seterr(divide="ignore", invalid="ignore")
    BSIdata = ((Band11Data+Band4Data)-(Band8Data+Band2Data))/((Band11Data+Band4Data)+(Band8Data+Band2Data))
    
    # Initiate raster and save to folder
    Driver = gdal.GetDriverByName("GTiff")
    BSIraster = Driver.Create(PathAndTifName, Band2Raster.RasterXSize, Band2Raster.RasterYSize, 1, gdal.GDT_Float32)
    BSIraster.SetProjection(Band2Raster.GetProjectionRef())
    BSIraster.SetGeoTransform(Band2Raster.GetGeoTransform())
    
    BSIrasterBand = BSIraster.GetRasterBand(1)
    BSIrasterBand.WriteArray(BSIdata)
    BSIraster = None

    # Close opened bands
    Band2Raster = None
    Band4Raster = None
    Band8Raster = None
    Band11Raster = None

########################################################################################################################################

def CalculateAllIndexes(ProductToProcessFolder, ProductToProcessName):
    """
    This function calculates indices (NDVI,FDI,FAI,SI,NDWI,NRD,NDMI,BSI) from inputs bands and saves as tif file.
    Input: ProductToProcessFolder - Location of Products Folder (ACOLITEProducts foder or Masked Bands folder).  
           ProductToProcessName - Specific folder name containing all bands for each product.
    Output: indexes tif file. 
    """
    
    ProductToProcess = os.path.join(ProductToProcessFolder,ProductToProcessName)
    S2platform = os.path.basename(ProductToProcess)[0:3]
    # List of band paths 
    ListOfBandPathsSorted = GenerateTifPaths(ProductToProcess, ["B01","B02","B03","B04","B05","B06","B07","B08","B8A","B11","B12"])
    # NDVI
    # Bands of Interest
    B8Path = ListOfBandPathsSorted[7]
    B4Path = ListOfBandPathsSorted[3]
    # Calculation
    NDVIPathAndTifName = os.path.join(ProductToProcess, "NDVI.tif")
    CalculateNormalizedIndexTif([B8Path,B4Path], NDVIPathAndTifName)  
    # FDI
    # Bands of Interest
    B6Path = ListOfBandPathsSorted[5]
    B11Path = ListOfBandPathsSorted[9]
    # Calculation
    FDIPathAndTifName = os.path.join(ProductToProcess, "FDI.tif")
    CalculateFAIorFDItif([B4Path, B6Path, B8Path, B11Path], S2platform, FDIPathAndTifName, Index='FDI')
    # FAI
    # Calculation
    FAIPathAndTifName = os.path.join(ProductToProcess, "FAI.tif")
    CalculateFAIorFDItif([B4Path, B6Path, B8Path, B11Path], S2platform, FAIPathAndTifName, Index='FAI')
    # SI
    # Bands of Interest
    B2Path = ListOfBandPathsSorted[1]
    B3Path = ListOfBandPathsSorted[2]
    # Calculation
    SIPathAndTifName = os.path.join(ProductToProcess, "SI.tif")
    CalculateSITif([B2Path,B3Path,B4Path], SIPathAndTifName)
    # NDWI
    # Calculation
    NDWIPathAndTifName = os.path.join(ProductToProcess, "NDWI.tif")
    CalculateNormalizedIndexTif([B3Path,B8Path], NDWIPathAndTifName)                      
    # NRD
    # Calculation
    NRDPathAndTifName = os.path.join(ProductToProcess, "NRD.tif")
    CalculateNRDTif([B8Path,B4Path], NRDPathAndTifName)                  
    # NDMI
    # Calculation
    NDMIPathAndTifName = os.path.join(ProductToProcess, "NDMI.tif")
    CalculateNormalizedIndexTif([B8Path,B11Path], NDMIPathAndTifName)                      
    # BSI
    # Calculation
    BSIPathAndTifName = os.path.join(ProductToProcess, "BSI.tif")
    CalculateBSITif([B2Path,B4Path,B8Path,B11Path], BSIPathAndTifName)                  