#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
Sentinel-2 L2 (after aplying ACOLITE on S2L1C) processing functions for masking and calculate indices.

@author: AIR Centre
"""

### Import Libraries ###################################################################################################################
from osgeo import osr, gdal
from terracatalogueclient import Catalogue
from shapely.geometry import box
import os

########################################################################################################################################
def create_features_stack(input_folder, output_folder):
    """
    This function creates a stack of features and saves into a single TIF.
    It deletes the isolated feature TIFs after creating the stack.
    Input: input_folder - Path to the folder where the isolated features are saved. String.
           output_folder - Path to the folder where the single stack will be saved. String.
    Output: Single stack of features as TIF file.
    """
    sorting_pattern = ('B01', 'B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B8A', 'B11', 
                    'B12') + ('NDVI', 'FAI', 'FDI', 'SI', 'NDWI', 'NRD', 'NDMI', 'BSI')
    paths_list = [os.path.join(input_folder, feature+".tif") for feature in sorting_pattern]

    virtual_stack = gdal.BuildVRT('', paths_list, separate=True)

    i = 1
    for feature in sorting_pattern:
        virtual_stack_band = virtual_stack.GetRasterBand(i)
        virtual_stack_band.SetDescription(feature)
        i += 1

    gdal.Translate(os.path.join(output_folder, os.path.basename(output_folder) +'_stack.tif'), virtual_stack, format='GTiff')
    virtual_stack = None

    # Delete isolated features, redundant information
    for tif_file in paths_list: 
        os.remove(tif_file)
   

########################################################################################################################################
def stack_info(stack_path):
    """
    This function provides basic information about a stack.
    Input: stack_path - Path to the stack TIF file.
    Output: stack_epsg, stack_res, stack_bounds, stack_size - Stack information.
    """
    # Open stack
    stack = gdal.Open(stack_path)

    # Get projection EPSG
    stack_proj = osr.SpatialReference(wkt=stack.GetProjection())
    stack_epsg = str(stack_proj.GetAttrValue('AUTHORITY',1))

    # Get basic info
    ulx, xres, _, uly, _, yres  = stack.GetGeoTransform()
    stack_res = [xres,yres]

    # Calculate bounds
    lrx = ulx + (stack.RasterXSize * xres)
    lry = uly + (stack.RasterYSize * yres)
    stack_bounds = [ulx, uly, lrx, lry]

    # Stack size
    x_size = stack.RasterXSize
    y_size = stack.RasterYSize
    stack_size = [x_size, y_size]
    
    return stack_epsg, stack_res, stack_bounds, stack_size

#################################################################################################
def TransformBounds_EPSG(OriginalBounds, SourceEPSG, TargetEPSG = 4326):
    """
    This function transforms a list of bounds from source EPSG to target EPSG.
    Input:  OriginalBounds - List of bounds [ulx, uly, lrx, lry].
            SourceEPSG - EPSG of original bounds as number.
            TargetEPSG - Desired EPSG as number to reproject the original bounds. Default is 4326.
    Output: TransformedBounds - List of tranformed bounds [ul_lon, lr_lat, lr_lon, ul_lat].
    """

    # Source projection
    SourceProj = osr.SpatialReference()
    SourceProj.ImportFromEPSG(SourceEPSG)
    
    # Target projection
    TargetProj = osr.SpatialReference()
    TargetProj.ImportFromEPSG(TargetEPSG)

    # Transformation
    Transform = osr.CoordinateTransformation(SourceProj, TargetProj)
    
    # Transform bounds 
    ul_lat, ul_lon, _ = Transform.TransformPoint(OriginalBounds[0], OriginalBounds[1])
    lr_lat, lr_lon, _ = Transform.TransformPoint(OriginalBounds[2], OriginalBounds[3])
    TransformedBounds = [ul_lon, lr_lat, lr_lon, ul_lat]
    
    # Create box(minx, miny, maxx, maxy, ccw=True) from bounds
    B2geometry = box(*TransformedBounds)
    
    return TransformedBounds, B2geometry

#################################################################################################
def Download_WorldCoverMaps(TerraScopeCredentials, SboxGeometry, ProcessingFolder):
    """
    This function uses an area of interest geometry to download WorldCover maps from TerraScope.
    https://vitobelgium.github.io/terracatalogueclient/installation.html
    Input: TerraScopeCredentials - TerraScope login info as list of strings [username, password].
           SboxGeometry - Shapely box geometry created with EPSG4326 bounds, this represents the Area of Interest. 
           ProcessingFolder - Folder path where the WorldCover maps will be placed.
    Output: LogList - Function's log outputs. List of strings.
            NonExistTile - Flag to inform if the user is trying to download a non-existing tile. Boolean.
    """
    OutputLog = ""
    LogList = [OutputLog]
    print(OutputLog)

    # Initiate TerraScope catalogue
    catalogue = Catalogue()

    # Filter catalogue by geometry
    products = catalogue.get_products("urn:eop:VITO:ESA_WorldCover_10m_2021_V2", geometry=SboxGeometry)
    
    NonExistTile = True
    for product in products:
        NonExistTile = False
        # Authentication and download
        catalogue.authenticate_non_interactive(username=TerraScopeCredentials[0], password=TerraScopeCredentials[1])
        TileName = str(product.title)
        OutputLog = "Downloading: " + TileName
        LogList.append(OutputLog)
        print(OutputLog)
        if not os.path.exists(os.path.join(ProcessingFolder, TileName+"_Map.tif")):
            catalogue.download_file(product.data[0], ProcessingFolder)
            OutputLog = "Done."
            LogList.append(OutputLog)
            print(OutputLog)
        else:
            OutputLog = "Ignoring download, since tile already exists."
            LogList.append(OutputLog)
            print(OutputLog)

    # In the middle of the ocean there are no worldcover tiles to download, when trying to download one of those non-existing tiles
    # the API doesn't return any status. Here, if the script doesnt enter the for loop is because it is a non-existing tile in the 
    # middle of the ocean, so we output a flag.
    if NonExistTile == True:
        OutputLog = "Trying to download a non-existing tile in the middle of the ocean."
        LogList.append(OutputLog)
        print(OutputLog)

    return LogList, NonExistTile