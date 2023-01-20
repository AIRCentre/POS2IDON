#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
Sentinel-2 L2 (after aplying ACOLITE on S2L1C) processing functions for masking and calculate indices.

@author: AIR Centre
"""

### Import Libraries ###################################################################################################################
from osgeo import osr
from terracatalogueclient import Catalogue
from shapely.geometry import box
import os

########################################################################################################################################
def Raster_MainInfo(Raster):
    """
    This function outputs and prints the main information about a raster.
    Input: Raster - GDAL opened raster.
    Output: (Projection, Resolution, Bounds, Size) as tuple. 
    """

    #Get projection EPSG and print it
    RasterProjection = osr.SpatialReference(wkt=Raster.GetProjection())
    RasterEPSG = str(RasterProjection.GetAttrValue('AUTHORITY',1))

    # Get some information and print Spatial Resolution
    ulx, xres, xskew, uly, yskew, yres  = Raster.GetGeoTransform()

    # Calculate remaining bounds and print them
    lrx = ulx + (Raster.RasterXSize * xres)
    lry = uly + (Raster.RasterYSize * yres)

    # Print raster size
    xSize = Raster.RasterXSize
    ySize = Raster.RasterYSize
    
    return (RasterEPSG, [xres,yres], [ulx, uly, lrx, lry], [xSize, ySize])

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