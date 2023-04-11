#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
Tiling functions to prepare dataset for prediction with U-Net.

@author: AIR Centre
"""

### Import Libraries ###################################################################################################################

import os
import glob
import itertools
from osgeo import gdal
import numpy as np
import rasterio as rio
import shutil

#######################################################################################################################################
def start_points(size, split_size, overlap=0):
    """
    From: https://github.com/Devyanshu/image-split-with-overlap
    """
    points = [0]
    stride = int(split_size * (1-overlap))
    counter = 1
    while True:
        pt = stride * counter
        if pt + split_size >= size:
            if split_size == size:
                break
            points.append(size - split_size)
            break
        else:
            points.append(pt)
        counter += 1
    return points

def split_image_with_overlap(folder_path, patch_size, overlap=0):
    """
    This function splits any tif image containing stacked bands with any degree of overlap.
    Input: folder_path - Path to the folder containing the tif image, the folder and file must have same name. String.
           patch_size - Size of the patch in the format (width, height).
           overlap - Percentage of overlap (0-1).
    Output: Patches with stacks tif bands saved in folder called patches.
    """
    # Create folder to store patches
    patches_path = os.path.join(folder_path, "Patches")
    if not os.path.exists(patches_path):
        os.mkdir(patches_path)

    # Open stacked raster
    image_path = os.path.join(folder_path, os.path.basename(folder_path) + "_masked_stack.tif")
    image_open = gdal.Open(image_path,1)
    image = image_open.ReadAsArray()
    img_shape = image.shape
    img_height = img_shape[1]
    img_width = img_shape[2]
    #print("Image: " + str(img_width) + "x" + str(img_height))
    
    patch_width = patch_size[0]
    patch_height = patch_size[1]
    #print("Desired patch: " + str(patch_width) + "x" + str(patch_height))

    # Based on https://github.com/Devyanshu/image-split-with-overlap
    x_points = start_points(img_width, patch_width, overlap)
    y_points = start_points(img_height, patch_height, overlap)

    row_count = 0
    for y in y_points:
        column_count = 0
        for x in x_points:
            patch = image[:, y:y+patch_height, x:x+patch_width] 
            patch_nbands = patch.shape[0]
            #print("Processed patch: " + str(patch_nbands) + "," + str(patch.shape[2]) + "x" + str(patch.shape[1]))
            
            # Patch path
            patch_path = os.path.join(patches_path, str(patch_width)+'x'+str(patch_height)+"_patch_"+str(row_count)+"-"+str(column_count)+".tif")

            # Init patch saving
            driver = gdal.GetDriverByName("GTiff")
            patch_data = driver.Create(patch_path, patch_width, patch_height, patch_nbands, gdal.GDT_Float32)
            
            # Set georeference for the patch
            geo_transform = list(image_open.GetGeoTransform())
            geo_transform[0] = geo_transform[0] + x*geo_transform[1] + y*geo_transform[2]
            geo_transform[3] = geo_transform[3] + x*geo_transform[4] + y*geo_transform[5]
            patch_data.SetGeoTransform(tuple(geo_transform))    
            patch_data.SetProjection(image_open.GetProjection())

            # Write patch data to give path
            for band in range(0, patch_nbands):             
                patch_data.GetRasterBand(band+1).WriteArray(patch[band, :, :])
                patch_data.GetRasterBand(band+1).SetNoDataValue(np.NaN)
            patch_data.FlushCache()
            patch_data = None
              
            column_count += 1
        row_count += 1

    image_open = None

#######################################################################################################################################
def mosaic_two_patches(left_or_top, right_or_bottom, output_folder, counter, axis=0):
    """
    This function reads two overlapping patches that are adjacent and creates a mosaic image.
    Where the patches overlap, half of this area is removed in both patches.
    Modified after created by ChatGPT.
    Input: left_or_top (lot) - Left or Top TIF path.
           right_or_bottom (rob) - Right or Bottom TIF path. Same shape and same CRS as left_or_top.
                                   Must overlap left_or_top.
           output_folder - Folder where the final mosaic will be saved.
           counter - Integer to add to output file name, used if you want to apply the function
                     more times to mosaic the previous mosaic rows.
           axis - 0 if the patches overlap in the same row. 
                  1 if the patches overlap in the same column.
    Output: Mosaic image saved inside output_folder.
    """
    if axis==0:
        # Open the left and right TIFF files
        with rio.open(left_or_top) as lot_tif, rio.open(right_or_bottom) as rob_tif:
            # Calculate the overlap start and end based on the bounding boxes
            lot_left, lot_bottom, lot_right, lot_top = lot_tif.bounds
            rob_left, rob_bottom, rob_right, rob_top = rob_tif.bounds
            pixel_width = lot_tif.res[0]
            overlap_start = max(lot_left, rob_left)
            overlap_end = min(lot_right, rob_right)

            if overlap_start >= overlap_end:
                raise ValueError("The TIFF files do not overlap.")

            # Read the half of the overlapping area from the left TIFF
            lot_window = rio.windows.from_bounds(overlap_start, lot_bottom, overlap_start+(overlap_end-overlap_start)/2, lot_top, lot_tif.transform)
            lot_data = lot_tif.read(window=lot_window)

            # Read the half of the overlapping area from the right TIFF
            rob_window = rio.windows.from_bounds(overlap_start+(overlap_end-overlap_start)/2, rob_bottom, overlap_end, rob_top, rob_tif.transform)
            rob_data = rob_tif.read(window=rob_window)

            # Read the non-overlapping area from the left and right TIFFs
            lot_non_overlap_window = rio.windows.from_bounds(lot_left, lot_bottom, overlap_start, lot_top, lot_tif.transform)
            lot_non_overlap = lot_tif.read(window=lot_non_overlap_window)
            rob_non_overlap_window = rio.windows.from_bounds(overlap_end, rob_bottom, rob_right, rob_top, rob_tif.transform)
            rob_non_overlap = rob_tif.read(window=rob_non_overlap_window)

            # Calculate the width of the new TIFF file
            #new_width = lot_tif.width + rob_tif.width - lot_data.shape[2] - rob_data.shape[2]
            new_width = (rob_right-lot_left)/pixel_width

            # Create the new TIFF file with the concatenated data
            new_profile = lot_tif.profile
            new_profile.update(width=new_width, transform=rio.transform.from_bounds(lot_left, lot_bottom, rob_right, lot_top, new_width, lot_tif.height))
            new_data = np.concatenate((lot_non_overlap, lot_data, rob_data, rob_non_overlap), axis=2)

        with rio.open(os.path.join(output_folder, "mosaic_row-" + str(counter) + ".tif"), 'w', **new_profile) as new_tif:
            new_tif.write(new_data)
    else:
        # Open the top and bottom TIFF files
        with rio.open(left_or_top) as lot_tif, rio.open(right_or_bottom) as rob_tif:
            # Calculate the overlap start and end based on the bounding boxes
            lot_left, lot_bottom, lot_right, lot_top = lot_tif.bounds
            rob_left, rob_bottom, rob_right, rob_top = rob_tif.bounds
            pixel_height = lot_tif.res[1]
            overlap_start = max(lot_bottom, rob_bottom)
            overlap_end = min(lot_top, rob_top)

            if overlap_start >= overlap_end:
                raise ValueError("The TIFF files do not overlap.")

            # Read the half of the overlapping area from the top TIFF
            lot_window = rio.windows.from_bounds(lot_left, overlap_start+(overlap_end-overlap_start)/2, lot_right, overlap_end, lot_tif.transform)
            lot_data = lot_tif.read(window=lot_window)

            # Read the half of the overlapping area from the bottom TIFF
            rob_window = rio.windows.from_bounds(rob_left, overlap_start, rob_right, overlap_start+(overlap_end-overlap_start)/2, rob_tif.transform)
            rob_data = rob_tif.read(window=rob_window)

            # Read the non-overlapping area from the top and bottom TIFFs
            lot_non_overlap_window = rio.windows.from_bounds(lot_left, overlap_end, lot_right, lot_top, lot_tif.transform)
            lot_non_overlap = lot_tif.read(window=lot_non_overlap_window)
            rob_non_overlap_window = rio.windows.from_bounds(rob_left, rob_bottom, rob_right, overlap_start, rob_tif.transform)
            rob_non_overlap = rob_tif.read(window=rob_non_overlap_window)

            # Calculate the height of the new TIFF file
            #new_height = rob_tif.height + lot_tif.height - rob_data.shape[1] - lot_data.shape[1]
            new_height = (lot_top-rob_bottom)/pixel_height

            # Create the new TIFF file with the concatenated data
            new_profile = rob_tif.profile
            new_profile.update(height=new_height, transform=rio.transform.from_bounds(rob_left, rob_bottom, rob_right, lot_top, rob_tif.width, new_height))
            new_data = np.concatenate((lot_non_overlap, lot_data, rob_data, rob_non_overlap), axis=1)

        with rio.open(os.path.join(output_folder, "mosaic_column-" + str(counter) + ".tif"), 'w', **new_profile) as new_tif:
            new_tif.write(new_data)

#######################################################################################################################################
def mosaic_patches(input_folder, output_folder, final_mosaic_name):
    """
    This function reads overlapping patches and creates a mosaic image.
    Input: input_folder - Folder where the overlapping patches are saved.
                          The patches must follow the name convention 256x256_patch_0-0.tif,
                          widthxheight_patch_row-column.tif.
           output_folder - Folder where the Mosaics folder containing the final mosaics will be saved.
           final_mosaic_name - Name of the final mosaic.
    Output: Mosaic image saved inside output_folder.
    """
    # Create folder to store mosaics
    mosaics_folder = os.path.join(output_folder, "Mosaics")
    if not os.path.exists(mosaics_folder):
        os.mkdir(mosaics_folder)
    
    # List of patches to read
    patches_path_list = glob.glob(os.path.join(input_folder, "*.tif"))

    # Reference patch size name
    patch_size_str = os.path.basename(patches_path_list[0]).split('_')[0]

    # Reference patch indicator name
    patch_indicator_str = os.path.basename(patches_path_list[0]).split('_')[3]

    # Split each element of the list
    patches_split = [(int(os.path.basename(p).split('_')[2].split('-')[0]), 
                      int(os.path.basename(p).split('_')[2].split('-')[1])) for p in patches_path_list]
    
    # Sort the list by patch number
    patches_sorted = sorted(patches_split)

    # Group the list by the patch number
    groups = []
    for _, g in itertools.groupby(patches_sorted, lambda x: x[0]):
        groups.append(list(g))

    # Convert each element of the grouped list back to the original patch format
    patches_grouped = [[os.path.join(input_folder, patch_size_str+"_patch_"+str(k[0])+'-'+str(k[1])+"_"+patch_indicator_str) for k in group] for group in groups]
    
    # Cycle through patch groups, create mosaic of patches for each row
    j = 0
    for patch_row in patches_grouped:
        group_len = len(patch_row)
        i = 0
        left_patch = patch_row[i]
        while i < group_len-1:
            right_patch = patch_row[i+1] 
            mosaic_two_patches(left_patch, right_patch, mosaics_folder, j, axis=0)
            left_patch = os.path.join(mosaics_folder, "mosaic_row-" + str(j) + ".tif")
            i += 1
        j += 1

    # Create mosaic of each row mosaic
    row_mosaics_len = len(glob.glob(os.path.join(mosaics_folder, "*.tif")))
    i = 0
    top_patch = os.path.join(mosaics_folder, "mosaic_row-0.tif")
    while i < row_mosaics_len-1:
        bottom_patch = os.path.join(mosaics_folder, "mosaic_row-" + str(i+1) + ".tif")
        mosaic_two_patches(top_patch, bottom_patch, mosaics_folder, 0, axis=1)
        top_patch = os.path.join(mosaics_folder, "mosaic_column-0.tif")
        i += 1

    # Rename final mosaic and move to the outisde
    os.rename(os.path.join(mosaics_folder, "mosaic_column-0.tif"), os.path.join(mosaics_folder, final_mosaic_name+".tif"))
    shutil.copy(os.path.join(mosaics_folder, final_mosaic_name+".tif"), os.path.join(output_folder, final_mosaic_name+".tif"))

#######################################################################################################################################
# def create_stacked_masked_bands(folder_path):
#     """
#     This function creates stacked images of masked bands.
#     Input: folder_path - Path to the folder containing the masked outputs. String.
#     Output: Stacks tif bands into a single tif with same name as folder_path.
#     """
#     # Stacks tif masekd bands into a single tif
#     SortingPattern = ["B01","B02","B03","B04","B05","B06","B07","B08","B8A","B11","B12"] # Prevents confusion between B08 and B8A during sort.
#     ListOfBandPaths = [os.path.join(folder_path, Band+".tif") for Band in SortingPattern]

#     VirtualStack = gdal.BuildVRT('', ListOfBandPaths, separate=True)
#     gdal.Translate(os.path.join(folder_path, os.path.basename(folder_path) +'_StackedBands.tif'), VirtualStack, format='GTiff')
#     VirtualStack = None

#######################################################################################################################################
# from patchify import patchify
# import tifffile as tiff
# import numpy as np

# def CreatePatches(MaskedProductsFolder,ShortProductName):
#     """
#     This function creates patches of 256x256 pixels containing stacked-masked bands 
#     Input: MaskedProductsFolder - Path to the folder containing the masking outouts. String.
#         ShortProductName - Path to the folder containing the processed masked bands. String.
#     Output: 256x256 patches with stacks tif bands of masked bands 
#     """
#     Tilezize = 256 # final patches size x,y
#     Offset = 246 # Offset=256 means no overlap
#     #create folder to store patches
#     os.mkdir(os.path.join(MaskedProductsFolder,ShortProductName,'patches'))
#     # open stacked raster
#     ImageStackOriginal_Open = gdal.Open(os.path.join(MaskedProductsFolder,ShortProductName, ShortProductName +'_StackedBands.tif'),1)
#     ImageStackOriginal = ImageStackOriginal_Open.ReadAsArray()
#     # clip stacked raster in multiple of 256
#     NumPatch_x = ImageStackOriginal.shape[1] // Tilezize
#     NumPatch_y = ImageStackOriginal.shape[2] // Tilezize
#     ImageStack_Clip = np.array(ImageStackOriginal)[:,0:(NumPatch_x) * Tilezize,0:(NumPatch_y) * Tilezize]
#     # create patches
#     for x,startX in enumerate (range(0, ImageStack_Clip.shape[1], Offset)):
#         for y,startY in enumerate(range(0, ImageStack_Clip.shape[2], Offset)):
#             Patch = ImageStack_Clip[:, startX:startX + Tilezize,startY:startY + Tilezize]
#             PatchPath = os.path.join(MaskedProductsFolder,ShortProductName,'patches',str(x+1)+'_'+str(y+1)+".tif")
#             # initiate patch to given path 
#             driver = gdal.GetDriverByName("GTiff")
#             PatchData = driver.Create(PatchPath, Tilezize, Tilezize, Patch.shape[0], gdal.GDT_Float32)
#             # set georeference for the patch
#             GeoTransform = list(ImageStackOriginal_Open.GetGeoTransform())
#             GeoTransform[0] = GeoTransform[0] + startY*GeoTransform[1] + startX*GeoTransform[2]
#             GeoTransform[3] = GeoTransform[3] + startY*GeoTransform[4] + startX*GeoTransform[5]
#             PatchData.SetGeoTransform(tuple(GeoTransform))    
#             PatchData.SetProjection(ImageStackOriginal_Open.GetProjection())
#             # write patch data to give path
#             for i in range(0,Patch.shape[0]) :
#                 PatchData.GetRasterBand(i+1).WriteArray(Patch[i, :, :])
#                 PatchData.GetRasterBand(i+1).SetNoDataValue(0)
#             PatchData.FlushCache()
#             PatchData = None
#     ImageStackOriginal_Open=None


# #######################################################################################################################################
# def CreatePatches_Alternative(MaskedProductsFolder,ShortProductName): # it uses patchify package but final patches are not georeferenced, not use
#     """
#     This function creates patches of 256x256 pixels containing stacked-masked bands 
#     Input: MaskedProductsFolder - Path to the folder containing the masking outouts. String.
#         ShortProductName - Path to the folder containing the processed masked bands. String.
#     Output: 256x256 patches with stacks tif bands of masked bands 
#     """
    
#     #create folder to store patches
#     os.mkdir(os.path.join(MaskedProductsFolder,ShortProductName,'patches'))
#     # open raster
#     #ImageStackOriginal = tiff.imread(os.path.join(MaskedProductsFolder,ShortProductName, ShortProductName +'_StackedBands.tif'))
#     ImageStackOriginal = gdal.Open(os.path.join(MaskedProductsFolder,ShortProductName, ShortProductName +'_StackedBands.tif')).ReadAsArray()
#     # get projection
#     prj = (gdal.Open(os.path.join(MaskedProductsFolder,ShortProductName, ShortProductName +'_StackedBands.tif'))).GetGeoTransform()
#     # clip raster
#     patch_size = 256
#     patch_x = ImageStackOriginal.shape[1] // patch_size
#     patch_y = ImageStackOriginal.shape[2] // patch_size
#     size_x = (patch_x) * patch_size
#     size_y = (patch_y) * patch_size
#     ImageStack_Clip = np.array(ImageStackOriginal)[:,0:size_x,0:size_y]
#     # create single patches
#     for img in range(ImageStack_Clip.shape[0]):       
#         patches_img = patchify(ImageStack_Clip[img], (256, 256), step=256)  #Step=256 for 256 patches means no overlap
#         for i in range(patches_img.shape[0]):
#             for j in range(patches_img.shape[1]):
#                 single_patch_img = patches_img[i,j,:,:]
#                 tiff.imwrite(os.path.join(MaskedProductsFolder,ShortProductName,'patches', str(i)+str(j)+ '_' + str(img) + ".tif"), single_patch_img)
#     # stacks all bands into a single tif per patch
#     for x in range(patch_x):
#         for y in range(patch_y):
#             SortingPattern = ["_0","_1","_2","_3","_4","_5","_6","_7","_8","_9","_10"] # Prevents confusion during sort.
#             ListOfBandPaths = [os.path.join(MaskedProductsFolder,ShortProductName,'patches',str(x)+str(y)+ Band+".tif") for Band in SortingPattern]
#             VirtualStack = gdal.BuildVRT('', ListOfBandPaths, separate=True)
#             VirtualStack.SetProjection(prj)
#             gdal.Translate(os.path.join(MaskedProductsFolder,ShortProductName,'patches' ,str(x)+str(y)+ ".tif"), VirtualStack, format='GTiff')
#             VirtualStack = None
#             for band in ListOfBandPaths:
#                 os.remove(band)





