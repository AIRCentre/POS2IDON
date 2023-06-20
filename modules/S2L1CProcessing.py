#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
Sentinel-2 L1C processing functions for search, download, unzip and atmospheric correction.

@author: AIR Centre
"""

### Import Libraries ###################################################################################################################
from sentinelsat import SentinelAPI, geojson_to_wkt
import time
import glob
import os
import zipfile
import sys
from xml.dom import minidom
import shutil
import requests
from dotenv import load_dotenv, set_key
from datetime import datetime, timedelta

# Import FeLS (GitHub clone)
Basepath = os.getcwd()
sys.path.append(os.path.join(Basepath,'configs/fetchLandsatSentinelFromGoogleCloud-master'))
import fels as fels 
sys.path.append(os.path.join(Basepath,'configs/fetchLandsatSentinelFromGoogleCloud-master/fels'))
import sentinel2 as sentinel2

 # Import ACOLITE (GitHub clone)
sys.path.append(os.path.join(Basepath,'configs/acolite-main'))
import acolite as ac

########################################################################################################################################
def CollectDownloadLinkofS2L1Cproducts_GC(ROI, SensingPeriod, S2CatalogueFolder, OutputFolder):
    """
    This function searches Sentinel-2 Level-1C products based on user parameters from Google Cloud.
    Input:  ROI - Region of Interest according to SentinelHub EO Browser. Dictionary.
            SensingPeriod - StartDate and EndDate. Tuple of strings as ('YYYYMMDD','YYYYMMDD').
            S2CatalogueFolder - Folder path where the downloaded Sentinel2 catalogue and metadata will be saved. String.
            OutputFolder - Folder where list of urls will be saved. String.
    Output: List of downloading links in a txt file, if the products exist.
            LogList - Function's log outputs. List of strings.
    """
    # Convert SensingPeriod to YYYY-MM-DD
    StartDate = SensingPeriod[0][0:4] + "-" + SensingPeriod[0][4:6] + "-" + SensingPeriod[0][6:8]
    EndDate = SensingPeriod[1][0:4] + "-" + SensingPeriod[1][4:6] + "-" + SensingPeriod[1][6:8]

    # Search Products
    OutputLog = "Searching Sentinel-2 L1C products download links from Google Cloud based on User Inputs..."
    LogList = [OutputLog]
    print(OutputLog)
    # Run FeLS
    # Additional options for Fels
    # 'cloudcover=99', help= set limit for cloud cover, defaul=100
    # 'excludepartial=False', help='Exclude partial tiles', default=False
    # 'includeoverlap=False', help='Include scenes that overlap the geometry but do not completely contain it', default=False
    # 'reject_old', help='For S2, skip redundant old-format (before Nov 2016) images', default=False THIS OPTION IN THIS FUNCTION IS NOT CHANGING ANYTHING, THE URL CORRESPONDING TO THE OPER FILE IS STILL COLLECTED!
    urls = fels.run_fels(None, 'S2', StartDate, EndDate, cloudcover=99, geometry=ROI, outputcatalogs=S2CatalogueFolder, excludepartial=False, includeoverlap=True,list=True, dates= False,reject_old=True)
        
    OutputLog = "Done.\n"
    LogList.append(OutputLog)
    print(OutputLog)
    # Print number of products 
    NumberOfProducts = len(urls)
    OutputLog = str(NumberOfProducts) + " download links collected:"
    LogList.append(OutputLog)
    print(OutputLog)

    OutputLog = '\n'.join(urls) + "\n"
    # Save link to txt file
    text_file = open(os.path.join(OutputFolder, "S2L1CProducts_URLs.txt"), "wt")
    text_file.write('\n'.join(urls) + "\n")
    text_file.close()

    LogList.append(OutputLog)
    print(OutputLog)
    
    return LogList

########################################################################################################################################
def DownloadTile_from_URL_GC(url,S2L1CproductsFolder):
    """
    This function downloads Sentinel-2 Level-1C products using download link collected from Google Cloud catalogue.
    Input:  url - download link
            S2L1CproductsFolder - Folder path where the products will be saved. String.
    Output: S2L1C products.
            LogList - Function's log outputs. List of strings.
    """
    # Download Product
    SAFEFileName = url.split('/') [-1]
    OutputLog = "Downloading " + SAFEFileName
    LogList = [OutputLog]
    print(OutputLog)
    # Run FeLS function
    # 'reject_old', help='For S2, skip redundant old-format (before Nov 2016) images', default=False GIVES ERROR:  [Errno 13] Permission denied: 'C:\\Users\\ANDREA~1\\AppData\\Local\\Temp\\
    sentinel2.get_sentinel2_image(url, outputdir=S2L1CproductsFolder, overwrite=False, partial=False, noinspire=False, reject_old=True)
        
    OutputLog = "Done.\n"
    LogList.append(OutputLog)
    print(OutputLog)
    
    return LogList

########################################################################################################################################
def CollectDownloadLinkofS2L1Cproducts_COAH(COAHuser, COAHpass, ROI, SensingPeriod, OutputFolder):
    """
    This function searches Sentinel-2 Level-1C products based on user parameters from Copernicus Open Access Hub.
    Input:  COAHuser - Copernicus Open Access Hub user. String.
            COAHpass - Copernicus Open Access Hub password. String.
            ROI - Region of Interest according to SentinelHub EO Browser. Dictionary.
            SensingPeriod - StartDate and EndDate. Tuple of strings as ('YYYYMMDD','YYYYMMDD').
            OutputFolder - Folder where list of urls will be saved. String.
    Output: List of downloading links in a txt file, if the products exist.
            LogList - Function's log outputs. List of strings.
    """
    # Connect to API (This url may change in the future)
    OutputLog = "Connecting to COAH API..."
    LogList = [OutputLog]
    print(OutputLog)
    COAH_API = SentinelAPI(COAHuser, COAHpass, "https://apihub.copernicus.eu/apihub/") 
    OutputLog = "Done.\n"
    LogList.append(OutputLog)
    print(OutputLog)

    # Search Products
    OutputLog = "Searching for Sentinel-2 L1C products from Copernicus Open Access Hub based on User Inputs..."
    LogList.append(OutputLog)
    print(OutputLog)
    S2L1Cproducts = COAH_API.query(geojson_to_wkt(ROI), date=SensingPeriod, platformname="Sentinel-2", producttype=("S2MSI1C"), cloudcoverpercentage=(0,100))
    NumberOfProducts = len(S2L1Cproducts.keys())
    OutputLog = str(NumberOfProducts) + " download links collected:"
    LogList.append(OutputLog)
    print(OutputLog)

    urls = []
    for product in range(len(S2L1Cproducts.keys())):
        url = (((list(S2L1Cproducts.items()))[product][1])['link'])
        SAFEFileName = (((list(S2L1Cproducts.items()))[product][1])['title']) + '.SAFE'
        url_and_SAFEFileName = str(url +'/'+ SAFEFileName)
        urls.append(url_and_SAFEFileName)

    OutputLog = '\n'.join(urls) + "\n"
    # Save link to txt file
    text_file = open(os.path.join(OutputFolder, "S2L1CProducts_URLs.txt"), "wt")
    text_file.write('\n'.join(urls) + "\n")
    text_file.close()
    
    LogList.append(OutputLog)
    print(OutputLog)

    return LogList

########################################################################################################################################
def DownloadTile_from_URL_COAH(COAHuser, COAHpass,url,S2L1CproductsFolder,LTAattempt=1):
    """
    This function downloads Sentinel-2 Level-1C products using download link collected from Copernicus Open Access Hub catalogue.
    Input:  url - download link
            S2L1CproductsFolder - Folder path where the products will be saved. String.
    Output: S2L1C products.
            LogList - Function's log outputs. List of strings.
    """
    
    # Get product ID from url link
    ProductID = (url.split('/') [-3])[10:46]
    SAFEFileName = url.split('/') [-1]
    OutputLog = "Downloading " + SAFEFileName
    LogList = [OutputLog]
    print(OutputLog)
    
    # Initialize COAH API
    COAH_API = SentinelAPI(COAHuser, COAHpass, "https://apihub.copernicus.eu/apihub/") 
    APIstatus = None
    Attempt = 0
    while APIstatus is None:
        try:
            APIstatus = COAH_API.download(ProductID, directory_path=S2L1CproductsFolder)
            OutputLog = "Done.\n"
            LogList.append(OutputLog)
            print(OutputLog)
        except Exception as e:
            OutputLog = str(e)
            LogList.append(OutputLog)
            print(OutputLog)
            # Wait for 60 seconds
            time.sleep(60)
            Attempt += 1
            pass
        if Attempt == LTAattempt:
            break
    
    # Unzip downloaded .zip folder
    if os.path.exists("".join(glob.glob(os.path.join(S2L1CproductsFolder, "*.zip"))).replace("\\","/")):
        OutputLog = "Unzipping Product..."
        LogList.append(OutputLog)
        print(OutputLog)
        with zipfile.ZipFile("".join(glob.glob(os.path.join(S2L1CproductsFolder, "*.zip"))).replace("\\","/"),"r") as ProductZip:
            ProductZip.extractall(S2L1CproductsFolder)
        
        os.remove("".join(glob.glob(os.path.join(S2L1CproductsFolder, "*.zip"))).replace("\\","/"))
        OutputLog = "Done.\n"
        LogList.append(OutputLog)
        print(OutputLog)

    return LogList

#######################################################################################################################################
def generate_tokens(username, password, refresh_token=None):
    """
    This function generates the access and refresh tokens from Copernicus Data Space Ecosystem (CDSE).
    The access token can be generated using CDSE credentials or refresh token.
    Input:  username - CDSE user.
            password - CDSE password.
            refresh_token - Refresh token. If None, access token will be generated with credentials.
    Output: access_token - Access token.
            refresh_token - Refresh token.
    """
    try:
        # Current CDSE url
        url = 'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        # Check if refresh token already exists - Code from CDSE documentation
        if isinstance(refresh_token, str) and (refresh_token != ""):
            print("Generating access token from refresh token...")
            payload = {'grant_type': 'refresh_token',
                       'refresh_token': refresh_token,
                       'client_id': 'cdse-public'}
            response = requests.post(url, headers=headers, data=payload)
            response_code = response.status_code
            # Check responses for access
            if response_code == 401:
                print("401 Unauthorized - Using credentials to generate token.")
                use_credentials = True
            elif response_code == 400:
                print("400 Bad Request - Using credentials to generate token.")
                use_credentials = True
            elif response_code == 200:
                access_token = response.json()['access_token']
                use_credentials = False
                print("Done.")
            else:
                print(str(response_code) + " - Using credentials to generate token.")
                use_credentials = True
        else:
            use_credentials = True
        
        if use_credentials == True:
            print("Generating access and refresh tokens from credentials...")
            payload = {'grant_type': 'password',
                       'username': username,
                       'password': password,
                       'client_id': 'cdse-public'}
            response = requests.post(url, headers=headers, data=payload)
            response_code = response.status_code
            # Check responses for access
            if response_code == 401:
                print("401 Unauthorized - Check your credentials.")
                access_token = ""
                refresh_token = ""
            elif response_code == 200:
                access_token = response.json()['access_token']
                refresh_token = response.json()['refresh_token']
                print("Done.")
            elif response_code == 400:
                print("400 Bad Request - Check your credentials.")
                access_token = ""
                refresh_token = ""
            else:
                print(response_code)
                access_token = ""
                refresh_token = ""

    except Exception as e:
        print(str(e))
        access_token = "" 
        refresh_token = ""
    print("") 

    return access_token, refresh_token

#######################################################################################################################################
def save_tokens(access_token, refresh_token, env_path):
    """
    This function saves CDSE tokens inside an .env file.
    Input: access_token - CDSE access token. String.
           refresh_token - CDSE refresh token. String.
           env_path - Path to .env file, where the tokens will be saved. String.
    Output: Tokens saved in .env file.
    """
    # Check .env file
    if not os.path.exists(env_path):
        with open(env_path, "w") as f:
            # Write variables
            f.write('\n\n# CDSE Tokens\n')
            f.write('CDSE_ACCESS_TOKEN=' + access_token)
            f.write('\n')
            f.write('CDSE_REFRESH_TOKEN=' + refresh_token)
            f.write('\n\n')
    else:
        load_dotenv(env_path)
        set_key(env_path, "CDSE_ACCESS_TOKEN", access_token)
        set_key(env_path, "CDSE_REFRESH_TOKEN", refresh_token)

#######################################################################################################################################
def collect_s2l1c_CDSE(roi, sensing_period, output_folder):
    """
    This function searches Sentinel-2 Level-1C products based on user parameters from 
    Copernicus Data Space Ecosystem (CDSE). The IDs and Names of products are collected 
    inside a text file.
    Input:  roi - Region of Interest according to SentinelHub EO Browser. Dictionary.
            sensing_period - StartDate and EndDate. Tuple of strings as ('YYYYMMDD','YYYYMMDD').
            output_folder - Folder where list of IDs and Names will be saved. String.
    Output: List of collected products in a txt file.
    """
    # CDSE base url - Might change in the future
    base_url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
    
    # ROI
    polygon_0 = str(tuple([item for sublist in roi["coordinates"][0] for item in sublist]))
    polygon = ",".join([f"{a}{b}" for a, b in zip(polygon_0.split(",")[0::2], polygon_0.split(",")[1::2])])

    # Sensing Period
    start_date_in = datetime.strptime(sensing_period[0], "%Y%m%d") 
    start_date = start_date_in.strftime("%Y-%m-%d")
    end_date_plus1 = datetime.strptime(sensing_period[1], "%Y%m%d") + timedelta(days=1)
    end_date = end_date_plus1.strftime("%Y-%m-%d")

    # Search products
    print("Searching for Sentinel-2 L1C products on Copernicus Data Space Ecosystem...")
    url = base_url + "?$filter=Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and att/OData.CSC.StringAttribute/Value eq 'S2MSI1C') and ContentDate/Start ge {start_date}T00:00:00.000Z and ContentDate/End le {end_date}T00:00:00.000Z and OData.CSC.Intersects(area=geography'SRID=4326;POLYGON({polygon})')".format(start_date=start_date, end_date=end_date, polygon=polygon)
    response = requests.get(url)
    response_code = response.status_code
    if response_code in (200, 308):
        response_values = response.json()['value']
        if len(response_values) != 0:
            print("Found " + str(len(response_values)) + " products.")
            products_list = []
            for i in response_values:
                url_safe = base_url + "(" + i["Id"] + ")/$value/" + str(i["Name"])
                products_list.append(url_safe)    
        else:
            print("No products found.")
            products_list = []
    else:
        print("Response: " + str(response_code))

    # Save to text file
    text_file = open(os.path.join(output_folder, "S2L1CProducts_URLs.txt"), "wt")
    text_file.write('\n'.join(products_list) + "\n")
    text_file.close()
    print("")

#######################################################################################################################################
def download_s2l1c_CDSE(access_token, url_safe, output_folder):
    """
    This function downloads a Sentinel-2 Level-1C product using a download link collected from 
    Copernicus Data Space Ecosystem (CDSE).
    Input: access_token - Access token that gives permission to download.
           url_safe - product download link together with SAFE product name.
           output_folder - Folder path where the products will be saved. String.
    Output: Download of S2L1C product.
    """
    # Split url
    safe_file_name = url_safe.split('/')[-1]
    url = url_safe.replace("/"+safe_file_name,"")
    product_path = os.path.join(output_folder, safe_file_name[:-4]+".zip")

    # Download
    print("Downloading " + safe_file_name +"...")
    session = requests.Session()
    session.headers.update({'Authorization': 'Bearer {}'.format(access_token)})
    response = session.get(url, allow_redirects=False)
    while response.status_code in (301, 302, 303, 307):
        url = response.headers['Location']
        response = session.get(url, allow_redirects=False)

    if response.status_code in (200, 308):
        file = session.get(url, verify=True, allow_redirects=True)
        with open(product_path, 'wb') as f:
           f.write(file.content)
        print("Done.")
    else:
        print("Unable to download. Response: " + str(response.status_code))

    # Unzip
    if os.path.exists(product_path):
        with zipfile.ZipFile(product_path) as product_zip:
            product_zip.extractall(output_folder)
        # Delete zip
        os.remove(product_path)
    print("")

#######################################################################################################################################
def ACacolite(FilesToAC, OutputFolder, EDuser, EDpass, ROI):
    """
    This function applies atmospheric correction to Sentinel-2 L1C products using ACOLITE.
    Input: FilesToAC - List with paths (strings) of products to process.
           OutputFolder - Folder where the AC files will be saved. String.
           EDuser - EarthData user as string.
           EDpass - EarthData password as string.
           ROI - SentinelHub EOBrowser (https://apps.sentinel-hub.com/eo-browser/) dictionary format.
    Output: Atmospherically Corrected products (L2).
    """
    # Define settings
    settings = {}
    # Path to input .SAFE file
    settings['inputfile'] = FilesToAC
    # Path of output directory
    settings['output'] = OutputFolder
    # Enable use of ancillary data (ozone, water vapour and atmospheric pressure) from EARTH DATA
    # Add EARTH DATA credentials (using them or not is not making significant differences)
    settings['EARTHDATA_u'] = EDuser
    settings['EARTHDATA_p'] = EDpass
    # Clip input image to a ROI
    S = ROI['coordinates'][0][0][1]
    W = ROI['coordinates'][0][0][0]
    N = ROI['coordinates'][0][2][1]
    E = ROI['coordinates'][0][2][0]
    settings['limit'] = S, W, N, E
    # Dark Spectrum Fitting options: 
    # Aerosol correction (fixed/tiled is default)
    settings['dsf_aot_estimate'] = 'tiled'
    # Residual Glint correction  (False is default) (if True: Default or Alternative (only possible with "fixed" option) methods)
    settings['dsf_residual_glint_correction'] = True
    settings['dsf_residual_glint_correction_method'] = 'default'
    # Calculate Top of Atmosphere, Surface Reflectance and Rayleigh reflectance (as in MARIDA values from L2W files)
    RayBands = ['rhorc_442','rhorc_443','rhorc_492','rhorc_559','rhorc_560','rhorc_665','rhorc_704','rhorc_739','rhorc_740','rhorc_780','rhorc_783','rhorc_833','rhorc_864','rhorc_865','rhorc_1610','rhorc_1614','rhorc_2186','rhorc_2202']
    SurBands = ['rhos_442','rhos_443','rhos_492','rhos_559','rhos_560','rhos_665','rhos_704','rhos_739','rhos_740','rhos_780','rhos_783','rhos_833','rhos_864','rhos_865','rhos_1610','rhos_1614','rhos_2186','rhos_2202']
    settings['l2w_parameters'] = ['rhot_*'] + SurBands + RayBands
    # Control default produced outputs in output folder (currently set to obtain only the .tif for each atm.corrected band + pngs)
    # Produce RGB / L2W maps in output folder
    settings['rgb_rhot'] = True
    settings['rgb_rhos'] = True
    # Delete NetCDFs L1R, L2R, L2W .nc files in output folder
    settings['l1r_delete_netcdf'] = True
    settings['l2r_delete_netcdf'] = True
    settings['l2w_delete_netcdf'] = True
    # Delete settings and log files are deleted in output folder
    settings['delete_acolite_run_text_files'] = True
    # GeoTIFF export options for L2W files
    settings['l2w_export_geotiff'] = True
 
    # Run Acolite
    ac.acolite.acolite_run(settings)

#######################################################################################################################################
def CleanAndOrganizeACOLITE(AcoliteFolder, S2L1CproductsFolder, SAFEFileName):
    """
    This function delets unnecessary files and organizes the rest into folders.
    Input: AcoliteFolder - Path to the folder containing the processed ACOLITE bands. String.
    Output: Flags files are deleted, bands are organized into folders and sub-folders according to product name. Band names are changed.Surface reflectances bands organized in sub-folder. Stacks tif bands into a single tif
    """
    # Delete unnecessary flags files in output folder
    ListOfACOLITEflagsPaths = glob.glob(os.path.join(AcoliteFolder, "*flags.tif"))
    for FlagsFile in ListOfACOLITEflagsPaths:
        os.remove(FlagsFile)
    # Delete .png files in output folder
    for PNGtoDelete in glob.glob(os.path.join(AcoliteFolder, "*.png")): 
        os.remove(PNGtoDelete)

    # Organize into folders
    LogList = ['']
    ListOfACOLITEfilePaths = glob.glob(os.path.join(AcoliteFolder, "*.tif"))
    #Through message if the ROI falls 100% on the no data side of the partial tile.
    if len(ListOfACOLITEfilePaths) == 0:
        OutputLog = "ROI falls 100% on the no data side of the partial tile. Product excluded."
        LogList = [OutputLog]
        #deleting unnecessary original products files from S2L1CproductsFolder 
        ProductToDelete=os.path.join(S2L1CproductsFolder,SAFEFileName)
        shutil.rmtree(ProductToDelete)
    else: 
        DictionaryOfGroups = {}  
        for ACOLITEfilePath in ListOfACOLITEfilePaths:  
            FileNameSplitted = os.path.basename(ACOLITEfilePath).split('_')
            Key = '_'.join(FileNameSplitted[0:9]) 
            Group = DictionaryOfGroups.get(Key,[])
            Group.append(ACOLITEfilePath)  
            DictionaryOfGroups[Key] = Group 
        
        # Remove keys without .tif bands from dictionary. The ACOLITE process only produced one .png file without bands, because there is no data on ROI (see Google Cloud function).
        DictionaryOfGroupsCleaned = {Key: Value for Key, Value in DictionaryOfGroups.items() if len(Value) != 1}
        ACOLITEProductFolderName = Key

        #Avoid overwrite of results by ACOLITE for products with same SENSING TIME
        if os.path.exists(os.path.join(AcoliteFolder, ACOLITEProductFolderName)):
            OutputLog = "Product with same sensing time. Overwrite avoided. Product excluded."
            LogList = [OutputLog]
            # deleting unnecessary acolite products from ACOLITEproductsFolder
            for ACOLITEfiletoDelete in glob.glob(os.path.join(AcoliteFolder, "*.tif")): 
                os.remove(ACOLITEfiletoDelete)
            #deleting original products files from S2L1CproductsFolder
            ProductToDelete=os.path.join(S2L1CproductsFolder,SAFEFileName)
            shutil.rmtree(ProductToDelete)
            pass
        else:
            os.mkdir(os.path.join(AcoliteFolder, ACOLITEProductFolderName))
            for ACOLITEfilePath in DictionaryOfGroupsCleaned[ACOLITEProductFolderName]:
                os.rename(ACOLITEfilePath, os.path.join(AcoliteFolder, ACOLITEProductFolderName, os.path.basename(ACOLITEfilePath)))

            # Rename bands files inside each folder
            ACOLITEProductFolder = os.path.join(AcoliteFolder, ACOLITEProductFolderName)  
            # Associate bands wavelengths (keys) with IDs (values). Valid for S2A and S2B
            BandsWlsToIds = {'rhorc_442':'B01','rhorc_443':'B01','rhos_442':'rhos_B01','rhos_443':'rhos_B01','rhot_442':'rhot_B01','rhot_443':'rhot_B01',
                             'rhorc_492':'B02','rhos_492':'rhos_B02','rhot_492':'rhot_B02',
                             'rhorc_559':'B03','rhorc_560':'B03','rhos_559':'rhos_B03','rhos_560':'rhos_B03','rhot_559':'rhot_B03','rhot_560':'rhot_B03',
                             'rhorc_665':'B04','rhos_665':'rhos_B04','rhot_665':'rhot_B04',
                             'rhorc_704':'B05','rhos_704':'rhos_B05','rhot_704':'rhot_B05',
                             'rhorc_739':'B06','rhorc_740':'B06','rhos_739':'rhos_B06','rhos_740':'rhos_B06','rhot_739':'rhot_B06','rhot_740':'rhot_B06',
                             'rhorc_780':'B07','rhorc_783':'B07','rhos_780':'rhos_B07','rhos_783':'rhos_B07','rhot_780':'rhot_B07','rhot_783':'rhot_B07',
                             'rhorc_833':'B08','rhos_833':'rhos_B08','rhot_833':'rhot_B08',
                             'rhorc_864':'B8A','rhorc_865':'B8A','rhos_864':'rhos_B8A','rhos_865':'rhos_B8A','rhot_864':'rhot_B8A','rhot_865':'rhot_B8A',
                             'rhot_945':'rhot_B09','rhot_943':'rhot_B09',
                             'rhot_1373':'rhot_B10','rhot_1377':'rhot_B10',
                             'rhorc_1610':'B11','rhorc_1614':'B11','rhos_1610':'rhos_B11','rhos_1614':'rhos_B11','rhot_1610':'rhot_B11','rhot_1614':'rhot_B11',
                             'rhorc_2186':'B12','rhorc_2202':'B12','rhos_2186':'rhos_B12','rhos_2202':'rhos_B12','rhot_2186':'rhot_B12','rhot_2202':'rhot_B12'}
            
            # Change name of each ACOLITE band
            for ACOLITEfilePath in glob.glob(os.path.join(ACOLITEProductFolder, "*")):
                # Basename of default ACOLITE band and path without basename
                ACOLITEfileBasename = os.path.basename(ACOLITEfilePath)
                RemainingPath = os.path.dirname(ACOLITEfilePath)
                # Associate wavelength key with band ID. Add extension
                ACOLITEidBandBasename = BandsWlsToIds[ACOLITEfileBasename.split("_")[-2]+"_" + ACOLITEfileBasename.split("_")[-1][:-4]] + ".tif"
                # Rename files
                os.rename(ACOLITEfilePath, os.path.join(RemainingPath,ACOLITEidBandBasename))
            
            # Delete .png and logfiles (.txt) left on the folder
            for PNGtoDelete in glob.glob(os.path.join(AcoliteFolder, "*.png")): 
                os.remove(PNGtoDelete)
            for TxttoDelete in glob.glob(os.path.join(AcoliteFolder, "*.txt")): 
                os.remove(TxttoDelete)
            
            # Organize surface reflectances bands into sub-folder for each product
            # Create sub-folder
            os.mkdir(os.path.join(ACOLITEProductFolder, 'Surface_Reflectance_Bands'))
            # Move surface reflectances to subfolder
            ListOfSurfRefBand = glob.glob(os.path.join(ACOLITEProductFolder, "*rhos_*"))
            for SurfRef_Band in ListOfSurfRefBand:
                shutil.move(SurfRef_Band,(os.path.join(ACOLITEProductFolder, 'Surface_Reflectance_Bands')))
            
            # Organize top of atmosphere reflectances bands into sub-folder for each product
            # Create sub-folder
            os.mkdir(os.path.join(ACOLITEProductFolder, 'Top_Atmosphere_Bands'))
            # Move surface reflectances to subfolder
            ListOfTopAtmBand = glob.glob(os.path.join(ACOLITEProductFolder, "*rhot_*"))
            for TopAtm_Band in ListOfTopAtmBand:
                shutil.move(TopAtm_Band,(os.path.join(ACOLITEProductFolder, 'Top_Atmosphere_Bands')))
            
            # Create text file with SAFE file name inside
            with open(os.path.join(ACOLITEProductFolder, "Info.txt"), "w") as text_file:
                text_file.write(SAFEFileName)
                
    return LogList
           
#######################################################################################################################################
def Extract_ACOLITE_name_from_SAFE(SAFEProductFile):
    """
    This function extract ACOLITE name from SAFE metadata.

    Input: SAFEProductFile - SAFE Folder path where the original products are saved. String.
    Output: ACOLITESAFEnames - Same name as ACOLITEProductFolder.
    """
    # Get name for output folder same as ACOLITE outputs           
    xmlFile = ",".join(glob.glob(os.path.join(SAFEProductFile,'GRANULE/*/MTD_TL.xml'))).replace("\\","/")   
    xmlfile_Open = minidom.parse(xmlFile)
    xml_GeneralInfo = xmlfile_Open.firstChild
    xml_SensingTime = xml_GeneralInfo.getElementsByTagName('SENSING_TIME')
    SensingTime = xml_SensingTime[0].firstChild.data
    FileNameSplitted = os.path.basename(SAFEProductFile).split('_')
    Sensor = FileNameSplitted[1]
    Date = FileNameSplitted[2]
    ACOLITESAFEname = FileNameSplitted[0] + "_" + Sensor[0:3] + "_" + Date[0:4]+ "_" + Date[4:6]+ "_" + Date[6:8] + "_" + SensingTime[11:13] + "_" + SensingTime[14:16] + "_" + SensingTime[17:19] + "_" + FileNameSplitted[5]
            
    return ACOLITESAFEname
#######################################################################################################################################

