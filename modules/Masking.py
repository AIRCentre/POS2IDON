# -*- coding: utf-8 -*-
"""
Functions related to masking.

@author: AIR Centre
"""

### Import Libraries #############################################################################################################
import glob
import shutil
import os
from osgeo import gdal, osr
from scipy import ndimage
from s2cloudless import S2PixelCloudDetector
import numpy as np
import rasterio
from xml.dom import minidom
from rasterio.warp import reproject, Resampling
from scipy.ndimage import minimum_filter

# Import other Functions ##########################################################################################################
from modules.SpectralIndices import CalculateNormalizedIndexTif
from modules.Auxiliar import GenerateTifPaths

#######################################################################################################################################
def Create_Mask_fromWCMaps(MaskProduct, WorldCoverMapsFolder, DstEPSG, Bounds, SpatialRes, WCnonExistTile, BufferSize=0):
    """
    This function reads WorldCover maps (ESA*.tif files) from a folder and creates a Water mask. If exists more than one 
    WorldCover tile, the function merges all tiles into one. After that, the single tile is reprojected according to the 
    desired EPSG and clipped according to bounds.
    Input: ProductToMask - Folder where the final mask will be saved.
           WorldCoverMapsFolder - Path to the folder where the WorldCover maps are saved.
           DstEPSG - The desired EPSG as string.
           Bounds - Bounds with the same projection of DstEPSG. List as [ulx, uly, lrx, lry] or [xmin, ymax, xmax, ymin].
           SpatialRes - Spatial resolution (Square: SpatialRes x SpatialRes) based on desired EPSG.
           
           WCnonExistTile - If Download_WorldCoverMaps function tries to download a non-existing tile, a True flag is outputed.
                            This True flag is used here to create a mask with value 1 (water).  
           BufferSize - Size of buffer applied to land, if 0 buffer step is ignored.
    Output: In this mask the value 1 represents water and NaNs (since NaNs are used in WorldCover map as open ocean), the value 0 represents land.
            LogList - Function's log outputs. List of strings.
    """
    LogList = []

    ProductToMaskName = os.path.basename(MaskProduct)
    MaskFolder = os.path.join(MaskProduct, "Masks")

    if WCnonExistTile == True:
        # Create mask filled with 1 representing a non-existing tile in the middle of the ocean
        OutputLog = "Generating mask of non-existing WorldCover tile in the middle of the ocean."
        LogList.append(OutputLog)
        print(OutputLog)

        Driver = gdal.GetDriverByName("GTiff")
        MaskPath = os.path.join(MaskFolder, ProductToMaskName + "_WATER_Mask.tif")
        
        CRS = osr.SpatialReference()
        CRS.ImportFromEPSG(int(DstEPSG))
        CRS_wkt = CRS.ExportToWkt()

        RasterXSize = abs(int((Bounds[2] - Bounds[0]) / SpatialRes))
        RasterYSize = abs(int((Bounds[1] - Bounds[3]) / SpatialRes))

        Mask = Driver.Create(MaskPath,
                             RasterXSize,
                             RasterYSize,
                             1, #Number of bands to create in the output
                             gdal.GDT_Byte)
        Mask.SetProjection(CRS_wkt)
        # [xmin, xres, 0, ymax, 0, -yres]
        Mask.SetGeoTransform([Bounds[0], SpatialRes, 0, Bounds[1], 0, -SpatialRes]) 
        MaskBand = Mask.GetRasterBand(1)
        MaskBand.Fill(1)
        MaskBand = None
    else:
        # List ESA WorldCover maps inside folder
        WorldCoverMapsSaved_list = sorted(glob.glob(WorldCoverMapsFolder + "/ESA*.tif"))

        # Merge all WorldCover maps together (do this in memory: /vsimem/)
        ResampleAlgorithm = gdal.GRA_NearestNeighbour
        SingleWorldCoverMap = gdal.BuildVRT("/vsimem/ESA_WorldCover_10m_Map.vrt", WorldCoverMapsSaved_list, resampleAlg=ResampleAlgorithm)

        # Reproject and clip this single map to desired EPSG (convert to GTiff and do this in memory). Select desired resolution and bounds.
        SingleWorldCoverMapClipped = gdal.Warp("/vsimem/ESA_WorldCover_10m_Map_Reprojected.tif", SingleWorldCoverMap, format='GTiff', outputBounds=[Bounds[0], Bounds[3], Bounds[2], Bounds[1]], xRes=SpatialRes, yRes=SpatialRes, dstSRS="EPSG:"+DstEPSG, resampleAlg=ResampleAlgorithm, options=['COMPRESS=DEFLATE'])

        # Close Original World Cover Map
        #gdal.Unlink("/vsimem/ESA_WorldCover_10m_Map.vrt")
        SingleWorldCoverMap = None

        # Create the land/water mask by changing data values
    
        # Read data as array
        SingleWorldCoverMapBand = SingleWorldCoverMapClipped.GetRasterBand(1)
        SingleWorldCoverMapData = SingleWorldCoverMapBand.ReadAsArray()
    
        # Change data to match land = 0 and water (nans included) = 1
        MaskData = np.where(np.logical_or(SingleWorldCoverMapData==80, SingleWorldCoverMapData==0), 1, 0)

        # Apply buffer
        if BufferSize > 0:
            MaskData = minimum_filter(MaskData, size=2*BufferSize+1, mode='constant', cval=1)
    
        # Save the mask
        Driver = gdal.GetDriverByName("GTiff")
        MaskPath = os.path.join(MaskFolder, ProductToMaskName + "_WATER_Mask.tif")
        Mask = Driver.Create(MaskPath,
                            SingleWorldCoverMapClipped.RasterXSize,
                            SingleWorldCoverMapClipped.RasterYSize,
                            1, #Number of bands to create in the output
                            gdal.GDT_Byte)

        Mask.SetProjection(SingleWorldCoverMapClipped.GetProjectionRef())
        Mask.SetGeoTransform(SingleWorldCoverMapClipped.GetGeoTransform()) 
        MaskBand = Mask.GetRasterBand(1)
        MaskBand.WriteArray(MaskData)
        MaskBand = None
        SingleWorldCoverMapClipped = None


    OutputLog = "Done."
    LogList.append(OutputLog)
    print(OutputLog)

    return LogList

#################################################################################################################################
def Create_Mask_fromNDWI(ProductToMask, MaskingProductFolder, NDWIthreshold,NDWIDilation_Size):
    """
    This function creates a mask based on the NDWI from the ACOLITE corrected bands 3 and 8.
    The mask is created by thresholding the NDWI values by 0.5 to eliminate water-only pixels, and
    subsequently applying a morphological dilation on the binary mask, to create a safety buffer and be
    sure that the eventual floating material is not exlcuded.
    Input: ProductToMask - Path to the ACOLITE product folder where the Bands (3 and 8) are saved. String.
           MaskingProductFolder - Folder where the masks will be saved. String.
           NDWIthreshold - NDWI threshold value to create mask, default is 0.5. Float.
           NDWIDilation_Size - number of iteration to perform dilation (>= 1)
    Output: Creation of several NDWI based masks.
            LogList - Function's log outputs. List of strings.
    """

    ProductToMaskName = os.path.basename(ProductToMask)
    # List of band paths
    SurfRef_BandFolder = (os.path.join(ProductToMask, 'Surface_Reflectance_Bands'))
    ListOfMaskedBandPathsSorted = GenerateTifPaths(SurfRef_BandFolder, ["rhos_B01","rhos_B02","rhos_B03","rhos_B04","rhos_B05","rhos_B06","rhos_B07","rhos_B08","rhos_B8A","rhos_B11","rhos_B12"])

    # NDWI Calculation
    B3 = ListOfMaskedBandPathsSorted[2]
    B8 = ListOfMaskedBandPathsSorted[7]
    NDWIPathAndTifName = os.path.join(MaskingProductFolder, ProductToMaskName + "_NDWI.tif")
    CalculateNormalizedIndexTif([B3,B8], NDWIPathAndTifName)
        
    # Apply a thresholding on the NDWI and get a binary mask
    Open_NDWI = gdal.Open(NDWIPathAndTifName)
    NDWI_Data = Open_NDWI.GetRasterBand(1).ReadAsArray()
    NDWI_Thresholding = NDWI_Data < NDWIthreshold
    # Save thresholded NDWI
    NDWI_Thr_PathAndTifName = os.path.join(MaskingProductFolder, ProductToMaskName + '_NDWI_Thr.tif')
    Driver = gdal.GetDriverByName("GTiff")
    NIraster = Driver.Create(NDWI_Thr_PathAndTifName, Open_NDWI.RasterXSize, Open_NDWI.RasterYSize, 1, gdal.GDT_Byte)
    NIraster.SetProjection(Open_NDWI.GetProjectionRef())
    NIraster.SetGeoTransform(Open_NDWI.GetGeoTransform())
    NIrasterBand = NIraster.GetRasterBand(1)
    NIrasterBand.WriteArray(NDWI_Thresholding)
    NIraster = None
    
    # Apply a dilation on the thresholded NDWI mask 
    Open_NDWI_Thr = gdal.Open(NDWI_Thr_PathAndTifName)
    NDWI_Thr_Data = Open_NDWI_Thr.GetRasterBand(1).ReadAsArray()
    NDWI_Dil_PathAndTifName = os.path.join(MaskingProductFolder, ProductToMaskName + '_NDWI_Thr_Dil_Mask.tif')
    NDWI_Dilation = ndimage.binary_dilation(NDWI_Thr_Data, output = NDWI_Dil_PathAndTifName, iterations=NDWIDilation_Size).astype(NDWI_Thr_Data.dtype)
    # Save dilated NDWI_Thr
    Driver = gdal.GetDriverByName("GTiff")
    NIraster = Driver.Create(NDWI_Dil_PathAndTifName, Open_NDWI_Thr.RasterXSize, Open_NDWI_Thr.RasterYSize, 1, gdal.GDT_Byte)
    NIraster.SetProjection(Open_NDWI_Thr.GetProjectionRef())
    NIraster.SetGeoTransform(Open_NDWI_Thr.GetGeoTransform())
    NIrasterBand = NIraster.GetRasterBand(1)
    NIrasterBand.WriteArray(NDWI_Dilation)
    NIraster = None

    # Delete _NDWI and _NDWI_Thr (Comment if needed)
    # Close unwanted Tifs first
    Open_NDWI = None
    Open_NDWI_Thr = None
    if os.path.exists(NDWIPathAndTifName):
        os.remove(NDWIPathAndTifName)
    if os.path.exists(NDWI_Thr_PathAndTifName):
        os.remove(NDWI_Thr_PathAndTifName)
    
    OutputLog = "Done."
    LogList = [OutputLog]
    print(OutputLog)
    
    return LogList

#################################################################################################################################
def Create_Mask_fromBand8(ProductToMask, MaskingProductFolder, Band8threshold, Band8Dilation_Size):
    """
    This function creates a mask based on the corrected band 8 from the ACOLITE.
    The mask is created by thresholding the band 8 values values by a threshold (i.e. 0.03) to eliminate water-only pixels, and
    subsequently applying a morphological dilation on the binary mask, to create a safety buffer and be
    sure that the eventual floating material is not exlcuded.
    Input: ProductToMask - Path to the ACOLITE product folder where the stack with Band8 is saved. String.
           MaskingProductFolder - Folder where the masks will be saved. String.
           Band8threshold - Band 8 threshold value to create mask, default is 0.03. Float.
           Band8Dilation_Size - number of iteration to perform dilation (>= 1)
    Output: Creation of band 8 based masks.
            LogList - Function's log outputs. List of strings.
    """
    ProductToMaskName = os.path.basename(ProductToMask)
    # Get stack
    StackPath = os.path.join(ProductToMask, ProductToMaskName+"_stack.tif") 
    
    
    # Apply a thresholding on the band and get a binary mask
    Stack = gdal.Open(StackPath)
    Band8_Data = Stack.GetRasterBand(8).ReadAsArray()
    Band8_Thresholding = Band8_Data > Band8threshold
    
    # Save thresholded mask
    MaskB8_Thr_PathAndTifName = os.path.join(MaskingProductFolder, ProductToMaskName + "_Band8_Thr.tif")
    Driver = gdal.GetDriverByName("GTiff")        
    NIraster = Driver.Create(MaskB8_Thr_PathAndTifName, Stack.RasterXSize, Stack.RasterYSize, 1, gdal.GDT_Byte)
    NIraster.SetProjection(Stack.GetProjectionRef())
    NIraster.SetGeoTransform(Stack.GetGeoTransform())
    NIrasterBand = NIraster.GetRasterBand(1)
    NIrasterBand.WriteArray(Band8_Thresholding)
    NIraster = None

    # Apply a dilation on the thresholded mask 
    Open_MaskB8_Thr = gdal.Open(MaskB8_Thr_PathAndTifName)
    MaskB8_Thr_Data = Open_MaskB8_Thr.GetRasterBand(1).ReadAsArray()
    MaskB8_Dil_PathAndTifName = os.path.join(MaskingProductFolder, ProductToMaskName + "_Band8_Thr_Dil_Mask.tif")
    MaskB8_Dilation = ndimage.binary_dilation(MaskB8_Thr_Data, output = MaskB8_Dil_PathAndTifName, iterations=Band8Dilation_Size).astype(MaskB8_Thr_Data.dtype)
    
    # Save dilated mask
    Driver = gdal.GetDriverByName("GTiff")
    NIraster = Driver.Create(MaskB8_Dil_PathAndTifName, Open_MaskB8_Thr.RasterXSize, Open_MaskB8_Thr.RasterYSize, 1, gdal.GDT_Byte)
    NIraster.SetProjection(Open_MaskB8_Thr.GetProjectionRef())
    NIraster.SetGeoTransform(Open_MaskB8_Thr.GetGeoTransform())
    NIrasterBand = NIraster.GetRasterBand(1)
    NIrasterBand.WriteArray(MaskB8_Dilation)
    NIraster = None

    # Close opened rasters
    Stack = None
    Open_MaskB8_Thr = None

    # Delete intermediate mask (Comment if needed)
    if os.path.exists(MaskB8_Thr_PathAndTifName):
        os.remove(MaskB8_Thr_PathAndTifName)

    OutputLog = "Done."
    LogList = [OutputLog]
    print(OutputLog)
    
    return LogList

#################################################################################################################################
def Create_Nan_Mask(ProductToMask, MaskingProductFolder):
    """
    This function creates a mask based on the position of Nan values from the ACOLITE-corrected raster.
    Input: ProductToMask - Path to the ACOLITE product folder where the stack with Band8 is saved. String.
           MaskingProductFolder - Folder where the masks will be saved. String.
    Output: Creation of band Nan based mask.
            LogList - Function's log outputs. List of strings.
    """
    ProductToMaskName = os.path.basename(ProductToMask)
    # Get stack
    StackPath = os.path.join(ProductToMask, ProductToMaskName+"_stack.tif") 
    
    # Apply a thresholding on the band and get a binary mask
    Stack = gdal.Open(StackPath)
    Band1_Data = Stack.GetRasterBand(1).ReadAsArray()
    Nan_mask = np.isnan(Band1_Data)
    Band1_Data[Nan_mask] = 1
    Band1_Data[~Nan_mask] = 0
    
    # Save thresholded mask
    Mask_Nan_PathAndTifName = os.path.join(MaskingProductFolder, ProductToMaskName + "_NAN_Mask.tif")
    Driver = gdal.GetDriverByName("GTiff")        
    NIraster = Driver.Create(Mask_Nan_PathAndTifName, Stack.RasterXSize, Stack.RasterYSize, 1, gdal.GDT_Byte)
    NIraster.SetProjection(Stack.GetProjectionRef())
    NIraster.SetGeoTransform(Stack.GetGeoTransform())
    NIrasterBand = NIraster.GetRasterBand(1)
    NIrasterBand.WriteArray(Nan_mask)
    NIraster = None

    # Close opened rasters
    Stack = None

    OutputLog = "Done."
    LogList = [OutputLog]
    print(OutputLog)
    
    return LogList

########################################################################################################################################  
def CloudMasking_S2CloudLess_ROI_10m(ac_product_folder, MaskingProductFolder, S2CL_Threshold, S2CL_Average, S2CL_Dilation):
    """
    This function create cloud masks on Sentinel-2 Level-1C products based on s2_cloudless algorithm.
    The function is set up to process 10 bands at 10m resolution Performance of cloud masking is controlled by the following
    parameters:
    - threshold=0.8 ; Specifies the cloud probability threshold. All pixels with cloud probability above this threshold are masked as cloudy pixels. Default value is 0.4.
    - average_over=4 ; Size of the disk in pixels for performing convolution (averaging probability over pixels). Default value is 4. Value 0 means do not perform this post-processing step
    - dilation_size=1 ; Size of the disk in pixels for performing dilation (averaging probability over pixels). Default value is 2. Value 0 means do not perform this post-processing step.
    - average_over and dilation_size: these two parameters depend on the resolution. At 10m resolution the recommended values are 22 and 11, respectively.
      These two parameters have impact on size of the buffer region around the clouds.
    Input:  ACOLITE Top of Atmosphere reflectances.
            MaskingProductFolder - Folder where the masks will be saved. String.
    Output: Cloud masked product file at 10m spatial resolution (as .tif).
            LogList - Function's log outputs. List of strings.
    """
    # Get shape and reprojection info from reference band
    ReferenceImage = os.path.join(ac_product_folder, 'Top_Atmosphere_Bands', 'rhot_B02.tif')
    ac_product_name = os.path.basename(ac_product_folder)

    with rasterio.open(ReferenceImage) as scl:
        _ = scl.read()
        aff = scl.transform
        crs = scl.crs
    
    # List of images (rhot) to process (ordered): B01,B02,B04,B05,B08,B8A,B09,B10,B11,B12.
    ListofImages_rhot = []
    SortingPattern = ['rhot_B01','rhot_B02','rhot_B04','rhot_B05','rhot_B08','rhot_B8A','rhot_B09','rhot_B10','rhot_B11','rhot_B12']
    for band_rhot in SortingPattern:
        ListofImages_rhot.append(os.path.join(ac_product_folder, 'Top_Atmosphere_Bands', band_rhot  + '.tif'))

    # Create an array for each band
    ListofBandsArray = []
    for band_rhot in ListofImages_rhot:
        Band = gdal.Open(band_rhot)
        BandArray = np.array(Band.GetRasterBand(1).ReadAsArray())
        ListofBandsArray.append(BandArray) 
    # Create a list of arrays
    Bands = np.array([np.dstack(ListofBandsArray)])
    # Apply s2cloudless algorithm
    Cloud_Detector = S2PixelCloudDetector(threshold=S2CL_Threshold, average_over=S2CL_Average, dilation_size=S2CL_Dilation) # To process on all 13 bands add: all_bands=True
    Cloud_Probs = Cloud_Detector.get_cloud_probability_maps(Bands)
    Mask = Cloud_Detector.get_cloud_masks(Bands).astype(rasterio.uint8)
    # Write output cloud mask 
    tif_out_image = os.path.join(MaskingProductFolder, ac_product_name+'_CLOUD_Mask_10m.tif')
    with rasterio.open(tif_out_image, "w",  driver='GTiff', compress="lzw", height=Mask.shape[1], width=Mask.shape[2], count=1, dtype=rasterio.uint8, transform=aff, crs=crs) as dest:
        dest.write(Mask)
    # Write output cloud probability (Comment if needed)
    #with rasterio.open(os.path.join(MaskingProductFolder, ac_product_name+'_CLOUD_Prob_10m.tif'), "w",  driver='GTiff',compress="lzw",height=Cloud_Probs.shape[1],width=Cloud_Probs.shape[2],count=1,dtype=Cloud_Probs.dtype,nodata=255, transform=aff, crs=crs) as dest:
    #    dest.write(Cloud_Probs)
    
    OutputLog = "Done."
    LogList = [OutputLog]
    print(OutputLog)
        
    return LogList

#######################################################################################################################################
def CreateFinalMask(masked_product, NDWI_or_Band8_andS2cloudlessUIn = ['BAND8', False]):
    """
    This function reads Water Mask, NDWI Mask or Band 8 Mask (if exists) and Cloud Mask (if exists) from MaskingProductFolder and creates a final binary Mask from the combination. 
    Input: masked_product - Folder of the product where the Masks folder containing masks is saved. String.
           NDWI_or_Band8_andS2cloudlessUIn - A List containing the User Inputs for NDWI/BAND8 and Cloud Mask options. Default is ['BAND8' for NDWI or BAND8 mask, False for Cloud mask]. List [string , bool].
    Output: Final Mask resulting from available masks.
            LogList - Function's log outputs. List of strings.
            FinalMaskPath - Path to the final mask.
    """
    MaskingProductFolder = os.path.join(masked_product, "Masks")
    Name = os.path.basename(masked_product)
     
    # Pick WATER mask (always available)
    WaterMask = ",".join(glob.glob(os.path.join(MaskingProductFolder, "*WATER_Mask.tif"))).replace("\\","/")
    # Read data as array
    WaterMaskOpen = gdal.Open(WaterMask)
    WaterMaskData = WaterMaskOpen.GetRasterBand(1)
    WaterMaskRead = WaterMaskData.ReadAsArray()
    # Final Mask Path
    FinalMaskPath = os.path.join(MaskingProductFolder, Name + "_FINAL_Mask.tif")
     
    if NDWI_or_Band8_andS2cloudlessUIn[0] == 'NDWI' and NDWI_or_Band8_andS2cloudlessUIn[1] == True:
        
        OutputLog = "Creating FINAL Mask using ALL (WATER, NDWI and CLOUD) masks."
        LogList = [OutputLog]
        print(OutputLog)

        # Pick NDWI mask
        NDWIMask = ",".join(glob.glob(os.path.join(MaskingProductFolder, '*NDWI_Thr_Dil_Mask.tif'))).replace("\\","/")
        NDWIMaskOpen = gdal.Open(NDWIMask)
        NDWIMaskData = NDWIMaskOpen.GetRasterBand(1)
        NDWIMaskRead = NDWIMaskData.ReadAsArray()

        # Pick CLOUD mask
        CloudMask = ",".join(glob.glob(os.path.join(MaskingProductFolder, '*CLOUD_Mask_10m.tif'))).replace("\\","/")
        CloudMaskOpen = gdal.Open(CloudMask)
        CloudMaskData = CloudMaskOpen.GetRasterBand(1)
        CloudMaskRead = CloudMaskData.ReadAsArray()

        # Set 1 where WATER mask is == 1, CLOUD mask == 0 , NDWI mask = 1, 0 in the rest
        WaterCloudMask = np.where(np.logical_and(WaterMaskRead==1, CloudMaskRead==0), 1, 0)
        FinalMaskData = np.where(np.logical_and(WaterCloudMask==1, NDWIMaskRead==1), 1, 0)

        # Save the mask
        Driver = gdal.GetDriverByName("GTiff")
        FinalMask = Driver.Create(FinalMaskPath,CloudMaskOpen.RasterXSize,CloudMaskOpen.RasterYSize,1,gdal.GDT_Byte)
        FinalMask.SetProjection(CloudMaskOpen.GetProjectionRef())
        FinalMask.SetGeoTransform(CloudMaskOpen.GetGeoTransform()) 
        FinalMaskBand = FinalMask.GetRasterBand(1)
        FinalMaskBand.WriteArray(FinalMaskData)
        FinalMaskBand = None

        OutputLog = "Done."
        LogList.append(OutputLog)
        print(OutputLog)

    elif NDWI_or_Band8_andS2cloudlessUIn[0] == 'BAND8' and NDWI_or_Band8_andS2cloudlessUIn[1] == True:
        
        OutputLog = "Creating FINAL Mask using ALL (WATER, BAND 8 and CLOUD) masks."
        LogList = [OutputLog]
        print(OutputLog)

        # Pick BAND 8 mask
        Band8Mask = ",".join(glob.glob(os.path.join(MaskingProductFolder, '*Band8_Thr_Dil_Mask.tif'))).replace("\\","/")
        Band8MaskOpen = gdal.Open(Band8Mask)
        Band8MaskData = Band8MaskOpen.GetRasterBand(1)
        Band8MaskRead = Band8MaskData.ReadAsArray()

        # Pick CLOUD mask
        CloudMask = ",".join(glob.glob(os.path.join(MaskingProductFolder, '*CLOUD_Mask_10m.tif'))).replace("\\","/")
        CloudMaskOpen = gdal.Open(CloudMask)
        CloudMaskData = CloudMaskOpen.GetRasterBand(1)
        CloudMaskRead = CloudMaskData.ReadAsArray()

        # Set 1 where WATER mask is == 1, CLOUD mask == 0 , NDWI mask = 1, 0 in the rest
        WaterCloudMask = np.where(np.logical_and(WaterMaskRead==1, CloudMaskRead==0), 1, 0)
        FinalMaskData = np.where(np.logical_and(WaterCloudMask==1, Band8MaskRead==1), 1, 0)

        # Save the mask
        Driver = gdal.GetDriverByName("GTiff")
        FinalMask = Driver.Create(FinalMaskPath,CloudMaskOpen.RasterXSize,CloudMaskOpen.RasterYSize,1,gdal.GDT_Byte)
        FinalMask.SetProjection(CloudMaskOpen.GetProjectionRef())
        FinalMask.SetGeoTransform(CloudMaskOpen.GetGeoTransform()) 
        FinalMaskBand = FinalMask.GetRasterBand(1)
        FinalMaskBand.WriteArray(FinalMaskData)
        FinalMaskBand = None

        OutputLog = "Done."
        LogList.append(OutputLog)
        print(OutputLog)

    elif NDWI_or_Band8_andS2cloudlessUIn[0] == None and NDWI_or_Band8_andS2cloudlessUIn[1] == True:
       
        OutputLog = "Creating FINAL Mask using WATER Mask and CLOUD Mask..."
        LogList = [OutputLog]
        print(OutputLog)

        # Pick CLOUD mask
        CloudMask = ",".join(glob.glob(os.path.join(MaskingProductFolder, '*CLOUD_Mask_10m.tif'))).replace("\\","/")
        CloudMaskOpen = gdal.Open(CloudMask)
        CloudMaskData = CloudMaskOpen.GetRasterBand(1)
        CloudMaskRead = CloudMaskData.ReadAsArray()

        # Set 1 where WATER mask is == 1, CLOUD mask == 0 , 0 in the rest
        FinalMaskData = np.where(np.logical_and(WaterMaskRead==1, CloudMaskRead==0), 1, 0)

        # Save the mask
        Driver = gdal.GetDriverByName("GTiff")
        FinalMask = Driver.Create(FinalMaskPath,CloudMaskOpen.RasterXSize,CloudMaskOpen.RasterYSize,1,gdal.GDT_Byte)  
        FinalMask.SetProjection(CloudMaskOpen.GetProjectionRef())
        FinalMask.SetGeoTransform(CloudMaskOpen.GetGeoTransform()) 
        FinalMaskBand = FinalMask.GetRasterBand(1)
        FinalMaskBand.WriteArray(FinalMaskData)
        FinalMaskBand = None

        OutputLog = "Done."
        LogList.append(OutputLog)
        print(OutputLog)
          
    elif NDWI_or_Band8_andS2cloudlessUIn[0] == 'NDWI' and NDWI_or_Band8_andS2cloudlessUIn[1] == False:
       
        OutputLog = "Creating FINAL Mask using WATER Mask and NDWI Mask..."
        LogList = [OutputLog]
        print(OutputLog)
          
        # Pick NDWI mask
        NDWIMask = ",".join(glob.glob(os.path.join(MaskingProductFolder, '*NDWI_Thr_Dil_Mask.tif'))).replace("\\","/")
        NDWIMaskOpen = gdal.Open(NDWIMask)
        NDWIMaskData = NDWIMaskOpen.GetRasterBand(1)
        NDWIMaskRead = NDWIMaskData.ReadAsArray()

        # Set 1 where WATER mask is == 1, NDWI mask = 1, 0 in the rest
        FinalMaskData = np.where(np.logical_and(WaterMaskRead==1, NDWIMaskRead==1), 1, 0)      
              
        # Save the mask
        Driver = gdal.GetDriverByName("GTiff")
        FinalMask = Driver.Create(FinalMaskPath,NDWIMaskOpen.RasterXSize,NDWIMaskOpen.RasterYSize,1,gdal.GDT_Byte)
        FinalMask.SetProjection(NDWIMaskOpen.GetProjectionRef())
        FinalMask.SetGeoTransform(NDWIMaskOpen.GetGeoTransform()) 
        FinalMaskBand = FinalMask.GetRasterBand(1)
        FinalMaskBand.WriteArray(FinalMaskData)
        FinalMaskBand = None

        OutputLog = "Done."
        LogList.append(OutputLog)
        print(OutputLog)

    elif NDWI_or_Band8_andS2cloudlessUIn[0] == 'BAND8' and NDWI_or_Band8_andS2cloudlessUIn[1] == False:
       
        OutputLog = "Creating FINAL Mask using WATER Mask and BAND 8 Mask..."
        LogList = [OutputLog]
        print(OutputLog)
          
        # Pick BAND 8 mask
        Band8Mask = ",".join(glob.glob(os.path.join(MaskingProductFolder, '*Band8_Thr_Dil_Mask.tif'))).replace("\\","/")
        Band8MaskOpen = gdal.Open(Band8Mask)
        Band8MaskData = Band8MaskOpen.GetRasterBand(1)
        Band8MaskRead = Band8MaskData.ReadAsArray()

        # Set 1 where WATER mask is == 1, NDWI mask = 1, 0 in the rest
        FinalMaskData = np.where(np.logical_and(WaterMaskRead==1, Band8MaskRead==1), 1, 0)      
              
        # Save the mask
        Driver = gdal.GetDriverByName("GTiff")
        FinalMask = Driver.Create(FinalMaskPath,Band8MaskOpen.RasterXSize,Band8MaskOpen.RasterYSize,1,gdal.GDT_Byte)
        FinalMask.SetProjection(Band8MaskOpen.GetProjectionRef())
        FinalMask.SetGeoTransform(Band8MaskOpen.GetGeoTransform()) 
        FinalMaskBand = FinalMask.GetRasterBand(1)
        FinalMaskBand.WriteArray(FinalMaskData)
        FinalMaskBand = None

        OutputLog = "Done."
        LogList.append(OutputLog)
        print(OutputLog)

    else:
        OutputLog = "FINAL Mask corresponds to the WATER Mask."
        LogList = [OutputLog]
        print(OutputLog)
        # Pick WATER mask, make a copy and change name
        shutil.copy(WaterMask, FinalMaskPath)

    # Close rasters
    WaterMaskOpen = None
    NDWIMaskOpen = None
    CloudMaskOpen = None
    Band8MaskOpen = None
        
    return LogList, FinalMaskPath

#######################################################################################################################################
def mask_stack(ac_product_folder, masked_product_folder, filter_ignore_value):
    """
    This function uses a mask to filter the data in a stack TIF file and creates a new masked stack TIF. 
    It also removes negative reflectances (optional).
    Input: ac_product_folder - Product folder with atmospheric corrected stack TIF.
           masked_product_folder - Product folder with Masks folder inside where the mask is located.
           filter_ignore_value - Value of the mask to ignore.
    Output: Masked stack TIF saved inside masked_product_folder. 
    """
    ac_product_name = os.path.basename(ac_product_folder)
    stack_path = os.path.join(ac_product_folder, ac_product_name+"_stack.tif")
    stack = gdal.Open(stack_path)
    stack_size = [stack.RasterXSize, stack.RasterYSize]
    band_number = stack.RasterCount

    # Read mask as array
    masked_product_name = os.path.basename(masked_product_folder)
    mask_path = os.path.join(masked_product_folder, "Masks", masked_product_name+"_FINAL_Mask.tif")
    mask = gdal.Open(mask_path)
    mask_band = mask.GetRasterBand(1)
    mask_data = mask_band.ReadAsArray()

    # Init masked stack
    driver = gdal.GetDriverByName("GTiff")
    masked_stack_path = os.path.join(masked_product_folder, masked_product_name+"_masked_stack.tif")
    masked_stack = driver.Create(masked_stack_path, stack_size[0], stack_size[1], band_number, gdal.GDT_Float32)
    masked_stack.SetProjection(stack.GetProjectionRef())
    masked_stack.SetGeoTransform(stack.GetGeoTransform())

    for bn in range(1, band_number+1):
        band = stack.GetRasterBand(bn)
        band_name = band.GetDescription()
        no_data_val = band.GetNoDataValue()
        band_data = band.ReadAsArray()
        # Check if the mask can be used with the stack in terms of shape
        assert band_data.shape == mask_data.shape
        # Apply filter
        band_data[mask_data==filter_ignore_value] = no_data_val
        masked_band = masked_stack.GetRasterBand(bn)
        masked_band.SetDescription(band_name)
        masked_band.WriteArray(band_data)

    # Close
    stack = None
    masked_stack = None

#######################################################################################################################################
def mask_stack_later(folder_with_mosaic, masked_product_folder, filter_ignore_value):
    """
    This function is similar to mask_stack function, but used for Unet later masking  and applies and additional nan mask. 
    """
    # Read nan masks as array
    masked_product_name = os.path.basename(masked_product_folder)
    nan_mask_path = os.path.join(masked_product_folder, "Masks", masked_product_name+"_NAN_Mask.tif")
    nan_mask = gdal.Open(nan_mask_path)
    nan_mask_band = nan_mask.GetRasterBand(1)
    nan_mask_data = nan_mask_band.ReadAsArray()

    # Apply nan mask to mosaic
    folder_with_mosaic_name = os.path.basename(folder_with_mosaic)
    mosaic_path = glob.glob(os.path.join(folder_with_mosaic, "*_mosaic.tif"))[0]
    mosaic = gdal.Open(mosaic_path,gdal.GA_Update)
    mosaic_band = mosaic.GetRasterBand(1)
    mosaic_data = mosaic_band.ReadAsArray()
    assert nan_mask_data.shape == mosaic_data.shape
    mosaic_data[nan_mask_data == 1] = np.nan
    mosaic_band.WriteArray(mosaic_data)

    nan_mask = None
    mosaic = None

    # Apply final mask to mosaic
    mosaic = gdal.Open(mosaic_path)
    mosaic_size = [mosaic.RasterXSize, mosaic.RasterYSize]
 
    # Read mask as array
    masked_product_name = os.path.basename(masked_product_folder)
    mask_path = os.path.join(masked_product_folder, "Masks", masked_product_name+"_FINAL_Mask.tif")
    mask = gdal.Open(mask_path)
    mask_band = mask.GetRasterBand(1)
    mask_data = mask_band.ReadAsArray()

    # Create masked mosaic
    driver = gdal.GetDriverByName("GTiff")
    masked_mosaic_path = os.path.join(folder_with_mosaic, masked_product_name+"_masked_stack_unet")
    if folder_with_mosaic_name[:-1] == "sc_map":
        dtype = gdal.GDT_Byte
        masked_mosaic_path = masked_mosaic_path + "-scmap.tif"
    else:
        dtype = gdal.GDT_Float32
        masked_mosaic_path = masked_mosaic_path + "-probamap.tif"
    masked_mosaic = driver.Create(masked_mosaic_path, mosaic_size[0], mosaic_size[1], 1, eType=dtype)
    masked_mosaic.SetProjection(mosaic.GetProjectionRef())
    masked_mosaic.SetGeoTransform(mosaic.GetGeoTransform())
    band = mosaic.GetRasterBand(1)
    band_name = band.GetDescription()
    band_data = band.ReadAsArray()
    # Check if the mask can be used with the mosaic in terms of shape
    assert band_data.shape == mask_data.shape
    # Apply filter
    band_data[mask_data==filter_ignore_value] = 0
    masked_band = masked_mosaic.GetRasterBand(1)
    masked_band.SetDescription(band_name)
    masked_band.WriteArray(band_data)

    # Close
    mosaic = None
    masked_mosaic = None

#######################################################################################################################################
# def ApplyMask(Band, MaskPath, FilterIgnoreValue, RemoveNegReflect):
#     """
#     This function uses a mask to filter the data in a band. It also removes negative reflectances (optional).
#     Input: Band - GDAL band (GetRasterBand).
#            MaskPath - Path to the input Mask.
#            FilterIgnoreValue - Value of the mask to ignore.
#     Output: BandData - Band data after applying the mask, no negative reflectances (optional). 
#     """

#     # Read band as array and get no data value
#     BandData = Band.ReadAsArray()
#     NoDataVal = Band.GetNoDataValue()
    
#     # Read mask as array
#     Mask = gdal.Open(MaskPath)
#     MaskBand = Mask.GetRasterBand(1)
#     MaskData = MaskBand.ReadAsArray()
    
#     # Check if the mask can be used with the raster in terms of shape
#     assert BandData.shape == MaskData.shape 

#     # Apply filter
#     BandData[MaskData==FilterIgnoreValue] = NoDataVal
#     if RemoveNegReflect == True:
#         BandData[BandData<0] = NoDataVal

#     return BandData

########################################################################################################################################  
# def CloudMasking_S2CloudLess_FullTile_60m(S2L1CproductsSAFE, MaskingProductFolder, Bounds,S2CL_Threshold,S2CL_Average,S2CL_Dilation):
#     """
#     This function create cloud masks on Sentinel-2 Level-1C products based on s2_cloudless algorithm.
#     The function is set up to process 10 bands at 60m resolution. To change the resolution change the
#     reference image (B01=60m;B02=10m;B05=20m). Performance of cloud masking is controlled by the following
#     parameters: (, , ).
#     - threshold=0.8 ; Specifies the cloud probability threshold. All pixels with cloud probability above this threshold are masked as cloudy pixels. Default value is 0.4.
#     - average_over=4 ; Size of the disk in pixels for performing convolution (averaging probability over pixels). Default value is 4. Value 0 means do not perform this post-processing step
#     - dilation_size=1 ; Size of the disk in pixels for performing dilation (averaging probability over pixels). Default value is 2. Value 0 means do not perform this post-processing step.
#     Input:  S2L1CproductSAFE - SAFE folder path of S2L1C product. String.
#             MaskingProductFolder - Folder where the masks will be saved. String.
#             Bounds - Band reference bounds. List.
#     Output: Cloud masked product file at 10m spatial resolution (as .tif).
#             LogList - Function's log outputs. List of strings.
#     """
     
#     # Get shape and reprojection info from reference band
#     ReferenceImage = "".join(glob.glob(os.path.join(S2L1CproductsSAFE,'GRANULE/*/IMG_DATA/*B01*.jp2'))).replace("\\","/") # B01=processing at 60m; B02=at 10m; B05=at 20m
#     with rasterio.open(ReferenceImage) as scl:
#         ref = scl.read()
#         tmparr = np.empty_like(ref)
#         aff = scl.transform
#         crs = scl.crs
            
#     # List of images to resample (ordered): B01,B02,B03,B04,B05,B06,B07,B08,B8A,B09,B10,B11,B12. TCI is not considered.
#     SAFEimageIncomplete = glob.glob(os.path.join(S2L1CproductsSAFE,'GRANULE/*/IMG_DATA/*B*.jp2'))[0][:-7]
#     SortingPattern = ["B01","B02","B04","B05","B08","B8A","B09","B10","B11","B12"] # Prevents confusion between B08 and B8A during sort, and allows to select 10 bands (excluding B03,B06,B07) or 13 bands for s2cloudless
#     ImagesInsideSAFEsorted = []
#     for p in SortingPattern:
#         ImagesInsideSAFEsorted.append(SAFEimageIncomplete + p + ".jp2")

#     # Get number of processing baseline from xml
#     xmlFile_msi = ",".join(glob.glob(os.path.join(S2L1CproductsSAFE,'MTD_MSIL1C.xml'))).replace("\\","/") 
#     xmlfile_msi_Open = minidom.parse(xmlFile_msi)
#     xml_GeneralInfo_msi = xmlfile_msi_Open.firstChild
#     xml_ProcessingBaseline = xml_GeneralInfo_msi.getElementsByTagName('PROCESSING_BASELINE')
#     ProcessingBaseline =  float(xml_ProcessingBaseline[0].firstChild.data)
    
#     # Resample bands to designed resolution and create an array
#     ListofBandsArray = []
#     for Image in ImagesInsideSAFEsorted:
#         with rasterio.open(Image) as scl:
#             Band = scl.read() 
#             reproject(Band, tmparr, src_transform = scl.transform, dst_transform = aff, src_crs = scl.crs, dst_crs = scl.crs, resampling = Resampling.bilinear)
            
#             if ProcessingBaseline >= 04.00:
#                 BandArray = (tmparr[0]-1000)/10000.0
#             else:
#                 BandArray = tmparr[0]/10000.0
            
#             ListofBandsArray.append(BandArray)
#         Bands = np.array([np.dstack(ListofBandsArray)])
    
#     # Apply s2cloudless algorithm
#     Cloud_Detector = S2PixelCloudDetector(threshold=S2CL_Threshold, average_over=S2CL_Average, dilation_size=S2CL_Dilation) # To process on all 13 bands add: all_bands=True
#     Cloud_Probs = Cloud_Detector.get_cloud_probability_maps(Bands)
#     Mask = Cloud_Detector.get_cloud_masks(Bands).astype(rasterio.uint8)
    
#     # Write output cloud mask 
#     tif_out_image = os.path.join(MaskingProductFolder, os.path.basename(MaskingProductFolder) + '_CLOUD_Mask.tif')
#     with rasterio.open(tif_out_image,"w",  driver='GTiff', compress="lzw", height=Mask.shape[1], width=Mask.shape[2], count=1, dtype=rasterio.uint8, transform=aff, crs=crs) as dest:
#         dest.write(Mask)
    
#     # Resample cloud mask to target shape
#     with rasterio.open(tif_out_image) as dataset:
#         data = dataset.read(out_shape=(dataset.count,int(dataset.height * 6),int(dataset.width * 6))) # 6=resampling at 10m; 3= at 20 m; 1=at 60m
#         dst_transform = dataset.transform * dataset.transform.scale((dataset.width / data.shape[-1]),(dataset.height / data.shape[-2]))
#         dst_kwargs = dest.meta.copy() 
#         dst_kwargs.update({"transform": dst_transform,"width": data.shape[-1],"height": data.shape[-2]})
#     with rasterio.open(tif_out_image,"w",**dst_kwargs) as dataset_res:
#         dataset_res.write(data)
    
#     # Clip Cloud Mask to ROI
#     tif_out_image_clipped = os.path.join(MaskingProductFolder, os.path.basename(MaskingProductFolder) + '_CLOUD_Clip_Mask_60m.tif')
#     gdal.Warp(tif_out_image_clipped, tif_out_image, format='GTiff', outputBounds=[Bounds[0], Bounds[3], Bounds[2], Bounds[1]])

#     # # Write output cloud probability (Comment if needed)
#     # with rasterio.open(os.path.join(MaskingProductFolder, os.path.basename(MaskingProductFolder) + '_CLOUD_Prob.tif'), "w",  driver='GTiff',compress="lzw",height=Cloud_Probs.shape[1],width=Cloud_Probs.shape[2],count=1,dtype=Cloud_Probs.dtype,nodata=255, transform=aff, crs=crs) as dest:
#     #     dest.write(Cloud_Probs)
    
#     # # Resample cloud probability to target shape
#     # with rasterio.open(os.path.join(MaskingProductFolder, os.path.basename(MaskingProductFolder) + '_CLOUD_Prob.tif')) as dataset:
#     #     data = dataset.read(out_shape=(dataset.count,int(dataset.height * 6),int(dataset.width * 6)))#6=resampling at 10m; 3= at 20 m; 1=at 60m
#     #     dst_transform = dataset.transform * dataset.transform.scale((dataset.width / data.shape[-1]),(dataset.height / data.shape[-2]))
#     #     dst_kwargs = dest.meta.copy() 
#     #     dst_kwargs.update({"transform": dst_transform,"width": data.shape[-1],"height": data.shape[-2]})
#     # with rasterio.open(os.path.join(MaskingProductFolder, os.path.basename(MaskingProductFolder) + '_CLOUD_Prob.tif'),"w",**dst_kwargs) as dataset_res:
#     #     dataset_res.write(data)

#     # Delete CLOUD_MASK (Comment if needed)
#     if os.path.exists(tif_out_image):
#         os.remove(tif_out_image)
    
#     OutputLog = "Done."
#     LogList = [OutputLog]
#     print(OutputLog)
        
#     return LogList



 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
