# POS2IDON

Pipeline for Ocean Features Detection with Sentinel-2.

## Overview 

POS2IDON is a tool to detect suspected locations of floating marine debris, and other ocean features (e.g., floating macroalgae, ships, turbid water), in Sentinel- 2 satellite imagery using Machine Learning. The pipeline includes modules for data acquisition, pre-processing, and pixel-based classification using different ML models (e.g. Random Forest, XGBoost, Unet). Available models were trained with spectral signatures from events available in literature, in particularly from MARIDA library, and show satisfactory metrics. The data pipeline allows to detect large enough features that can be suspicious in terms of aggregation of floating plastic litter and therefore be used to alert and inform stakeholders. POS2IDON outputs include the classification maps for all the available Sentinel-2 imagery of a given region of interest and temporal period, specified by the user. By providing the source code, the vision is to share a transparent easy-to-examine, and flexible, code that is decomposed in several modules, and in this way stimulate improvements and new implementations from the scientific community. 

## Workflow

In this repository we propose an open-policy data pipeline framework for ocean features detection (e.g. marine debris, floating vegetation, foam and water) using Sentinel-2 satellite imagery and machine learning methods. The presented workflow consists of three main steps:

1) search and download Level-1C Sentinel-2 imagery from [Google Cloud Storage](https://cloud.google.com/storage/docs/public-datasets/sentinel-2) using [FeLS - Fetch Landsat & Sentinel Data from Google Cloud](https://github.com/vascobnunes/fetchLandsatSentinelFromGoogleCloud.git), [Copernicus Data Space Ecosystem](https://dataspace.copernicus.eu) using [CDSETool](https://github.com/SDFIdk/CDSETool.git) or [Copernicus Open Access Hub](https://scihub.copernicus.eu/) using [sentinelsat](https://github.com/sentinelsat/sentinelsat.git) (discontinued),  for a given region of interest and specified time period.

2) image pre-processing: application of [ACOLITE](https://github.com/acolite/acolite.git/) atmospheric correction module to obtain Rayleigh-corrected reflectances and surface reflectances, application of a land mask based on [ESA World Cover 2021](https://worldcover2021.esa.int/), application of a cloud mask computed with [Sentinel Hub's cloud detector for Sentinel-2 imagery](https://github.com/sentinel-hub/sentinel2-cloud-detector), application of “marine clear water” mask (NDWI-based, or a NIR-reflectance based thresholding) and NaN mask.

3) pixel-based classification with machine learning methods on the downloaded set of Sentinel-2 images. The workflow supports three well-known machine learning algorithms (Random Forest, XGBoost and Unet) trained with spectral signatures, as well as spectral indices (e.g., NDVI - Normalized Difference Vegetation Index, FAI - Floating Algae Index, FDI - Floating Debris Index). As additional option, the classification step using Unet, can be computed also with Julia programming language. Outputs include the classification maps and classification probability maps, for the chosen region and time period. For large regions of interest, one has the option to split the image for classification and then mosaic.

## Dependencies

### Python

POS2IDON is coded in Python 3.9. In the terminal, create a Python environment using [conda](https://www.anaconda.com), activate it, update pip:
```
conda create -n pos2idon-env python=3.9
conda activate pos2idon-env
pip install --upgrade pip
```

and install libraries in the following order (takes approx. 8-15 minutes):

*macOS:*
```
conda install -c conda-forge gdal=3.5.0 geopandas=0.11.1 s2cloudless=1.7.0 lightgbm=3.3.2 
pip install python-dotenv==0.20.0 cdsetool==0.1.3 zipfile36==0.1.3 netCDF4==1.5.8 pyproj==3.3.1 scikit-image==0.19.2 pyhdf==0.10.5 --extra-index-url https://artifactory.vgt.vito.be/api/pypi/python-packages/simple terracatalogueclient==0.1.11 matplotlib==3.5.2 pandas==1.4.3 scikit-learn==1.1.1 ubelt==1.1.2 rasterio==1.3.0.post1 hummingbird-ml==0.4.5 xgboost==1.7.3 juliacall==0.9.14 pyarrow==14.0.1
conda install -c pytorch pytorch=1.13.1 torchvision=0.14.1 torchaudio=0.13.1
```
*Windows:*
```
conda install -c conda-forge gdal=3.5.0 geopandas=0.11.1 lightgbm=3.3.2
pip install python-dotenv==0.20.0 cdsetool==0.1.3 zipfile36==0.1.3 netCDF4==1.5.8 pyproj==3.3.1 scikit-image==0.19.2 pyhdf==0.10.5 --extra-index-url https://artifactory.vgt.vito.be/api/pypi/python-packages/simple terracatalogueclient==0.1.11 matplotlib==3.5.2 pandas==1.4.3 scikit-learn==1.1.1 ubelt==1.1.2 rasterio==1.3.0.post1 hummingbird-ml==0.4.5 xgboost==1.7.3 s2cloudless==1.7.0 juliacall==0.9.14 pyarrow==14.0.1
conda install -c pytorch pytorch=1.13.1 torchvision=0.14.1 torchaudio=0.13.1
```
*Ubuntu:*
```
pip install --find-links=https://girder.github.io/large_image_wheels --no-cache GDAL==3.5.0
pip install geopandas==0.11.1 s2cloudless==1.7.0 pip install lightgbm==3.3.2
pip install python-dotenv==0.20.0 cdsetool==0.1.3 zipfile36==0.1.3 netCDF4==1.5.8 pyproj==3.3.1 scikit-image==0.19.2 pyhdf==0.10.5 --extra-index-url https://artifactory.vgt.vito.be/api/pypi/python-packages/simple terracatalogueclient==0.1.11 matplotlib==3.5.2 pandas==1.4.3 scikit-learn==1.1.1 ubelt==1.1.2 rasterio==1.3.0.post1 hummingbird-ml==0.4.5 xgboost==1.7.3 juliacall==0.9.14 pyarrow==14.0.1
pip install torch==1.13.1 torchvision==0.14.1 torchaudio==0.13.1
```

### Julia

1- To run the Unet classification step using Julia, check if you have Julia installed on your computer. Download [here](https://julialang.org/downloads/);

2- Run POS2IDON, the first time you run it `julicall` will install the latest version of Julia;

3- Locate your POS2IDON Julia environment, usually it is inside conda envs `pos2idon-env/julia_env` folder (macOS) or the base Julia `environments/pyjuliapkg` folder (Windows);

4- Open a terminal inside one of those folders and type `julia`;

5- Type `]` and write: 
```
activate .
add Flux BSON Glob CUDA cuDNN
``` 

6- Run POS2IDON again.

You only need to to this the first time you run POS2IDON.

We recommend a machine with a dedicated GPU.

## Configuration

- Get credentials for the followings data providers:

    -   [Copernicus Data Space Ecosystem](https://identity.dataspace.copernicus.eu/auth/realms/CDSE/login-actions/registration?client_id=cdse-public&tab_id=gpbsIrm5Zqs)
    -   [Copernicus Open Access Hub](https://scihub.copernicus.eu/dhus/#/home/) (discontinued)
    -   [Terrascope](https://sso.terrascope.be/auth/realms/terrascope/protocol/openid-connect/auth?client_id=terrascope-viewer&redirect_uri=https%3A%2F%2Fviewer.esa-worldcover.org%2Fworldcover%2F%3Flanguage%3Den%26bbox%3D-262.61718749999994%2C-79.6556678546481%2C262.61718749999994%2C79.65566785464813%26overlay%3Dfalse%26bgLayer%3DOSM%26date%3D2023-01-19%26layer%3DWORLDCOVER_2021_MAP&state=76f1db73-28b4-4e8b-8b41-21a995a5ee92&response_mode=fragment&response_type=code&scope=openid&nonce=1fa78ab3-bf00-4834-8213-f331e0046921)
    -   [NASA EarthData ](https://urs.earthdata.nasa.gov/home)

    and type them in the file `configs/Environments/.env`

- Place your saved Machine Learning models in :\
    `configs/MLmodels/YourModelFolder/YourModel.pkl` &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(for scikit-learn RF and XGB)\
    `configs/MLmodels/YourModelFolder/YourModel.zip` &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(for Py-Torch)\
    `configs/MLmodels/YourModelFolder/YourModel.pth` &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(for Python Unet)\
    `configs/MLmodels/YourModelFolder/YourModel.bson`&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(for Julia Unet)
    
- Execute the script `workflow.py`, this will automatically clone the following repositories:

    - [FeLS - Fetch Landsat & Sentinel Data from Google Cloud (private)](https://github.com/EmanuelCastanho/fetchLandsatSentinelFromGoogleCloud.git) repository in the folder :\
    `/configs/fetchLandsatSentinelFromGoogleCloud-master`

    - [ACOLITE - generic atmospheric correction module (20221114.0)](https://github.com/acolite/acolite.git/) repository in the folder :\
    `/configs/acolite-main`
   
If the cloning does not start automatically or if the repositories were corrupted during cloning, you can manually download them using the previous links.

The first time you run FeLS it will download a csv table, this process may take a few minutes.

## Settings and Usage

Open `configs/User_Inputs.py` and follow the descriptions to set up wanted workflow options, insert region of interest and sensing period, select download service, define masking and classification options. Execute the script `workflow.py` to run the workflow.

### Example

To test the classification workflow we provide a random forest model based on [MARIDA](https://github.com/marine-debris/marine-debris.github.io) spectral signatures library and trained as described in [Kikaki et al., 2022](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0262247). You can download the model folder using this [link](https://drive.google.com/drive/folders/1KtzX9tgvEOwhoRGW-fjy0qHpfdga_0sx) and place it in `configs/MLmodels`. By default the `User_Inputs.py` is configured to perform a classification on a [plastic debris event](https://sentinels.copernicus.eu/web/success-stories/-/copernicus-sentinel-2-show-dense-plastic-patches) case study that occurred in the Gulf of Honduras on 18th September 2020. 

![](Example-img.png)
Visualization with [QGIS](https://qgis.org/en/site/), color palette provided inside `configs/QGIScolorpalettes`.

## Citation

If you find POS2IDON useful in your research, acknowledge us using the following reference:

- A. Valente, E. Castanho, A. Giusti, J. Pinelo and P. Silva, "An Open-Source Data Pipeline Framework to Detect Floating Marine Plastic Litter Using Sentinel-2 Imagery and Machine Learning," IGARSS 2023 - 2023 IEEE International Geoscience and Remote Sensing Symposium, Pasadena, CA, USA, 2023, pp. 4108-4111, doi: [10.1109/IGARSS52108.2023.10281415](https://ieeexplore.ieee.org/document/10281415).

POS2IDON tool has been tested in the framework of different EU projects (LabPlas and EcoBlue) and under different data approaches.

POS2IDON is provided by AIR Centre as an experimental tool, without explicit or implied warranty. Use of the tool is at your own discretion and risk.
