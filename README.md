# POS2IDON
Pipeline for Ocean Features Detection with Sentinel-2.

## Objective 

The objective of this work is to foster the development of a tool for monitoring ocean features namely floating plastic accumulations, using satellite imagery. By providing the source code, the vision is to provide a transparent easy-to-examine code that can be decomposed in several modules, and in this way stimulate improvements and new implementations from the scientific community to reach the ultimate goal of tracking floating plastic in an operational manner from satellite data. 

## Workflow
In this repository we propose an open-policy data pipeline framework for ocean features detection (e.g. floating plastic patches, foam, floating macroalgae, turbid water and clear water) using Sentinel-2 satellite imagery and machine learning methods. The presented workflow consists of three main steps:

1) search and Download Level-1C Sentinel-2 imagery from [Copernicus Open Access Hub](https://scihub.copernicus.eu/) or [Google Cloud Storage](https://cloud.google.com/storage/docs/public-datasets/sentinel-2) for a given region of interest and specified time period.

2) image pre-processing : application of [ACOLITE](https://github.com/acolite/acolite.git/) atmospheric correction module to obtain Rayleigh-corrected reflectances and surface reflectances,
application of a cloud mask computed with [Sentinel Hub's cloud detector for Sentinel-2 imagery](https://github.com/sentinel-hub/sentinel2-cloud-detector), application of a land mask based on [ESA World Cover 2021](https://worldcover2021.esa.int/), application of “marine clear water” mask (NDWI-based, or a NIR-reflectance based thresholding).

3) pixel-based classification with machine learning methods on the downloaded set of Sentinel-2 images. The workflow supports two well-known machine learning decision-tree algorithms (Random Forest and XGBoost) trained with spectral signatures, as well as spectral indices (e.g., NDVI - Normalized Difference Vegetation Index, FAI - Floating Algae Index, FDI - Floating Debris Index). As additional option, the classification step, using Random Forest trained models, can be computed also with Julia programming language. Outputs include the classification maps and classification probability maps, for the chosen region and time period.

## Dependencies
### Python
POS2IDON is coded in Python 3. Create and activate a Python environment using conda:
```
conda create -n Pipeline-Env python=3.9
conda activate Pipeline-Env
```
and install following libraries in this order:
```
conda install -c conda-forge gdal=3.5.0 geopandas=0.11.1 lightgbm=3.3.2
```
```
pip install python-dotenv==0.20.0 sentinelsat==1.1.1 zipfile36==0.1.3 netCDF4==1.5.8 pyproj==3.3.1 scikit-image==0.19.2 pyhdf==0.10.5 --extra-index-url https://artifactory.vgt.vito.be/api/pypi/python-packages/simple terracatalogueclient==0.1.11 matplotlib==3.5.2 y pandas==1.4.3 scikit-learn==1.1.1 ubelt==1.1.2 s2cloudless==1.6.0 rasterio==1.3.0.post1 hummingbird-ml==0.4.5 julia xgboost 
```

### Julia
To run the classification step using [Julia programming language](https://julialang.org/downloads/) is necessary to install locally a version julia (1.8.3 tested) with the following packages:
[DataFrames.jl](https://github.com/JuliaData/DataFrames.jl), [DecisionTree.jl](https://github.com/JuliaAI/DecisionTree.jl) ,[JLD2.jl](https://github.com/JuliaIO/JLD2.jl),[Pandas.jl](https://github.com/JuliaPy/Pandas.jl) [PyCall](https://github.com/JuliaPy/PyCall.jl).

This has been tested successfully on Windows (11) machine in VSCode. The Julia function is contained in `Functions/Classification.jl` and is called using [PyJulia](https://github.com/JuliaPy/pyjulia) as python interface to julia. To correctly set-up the interfacing of Python with Julia this [link](https://syl1.gitbook.io/julia-language-a-concise-tutorial/language-core/interfacing-julia-with-other-languages) can be useful.

## Configurations

- Clone the followings repositories (if the cloning does not start automatically):

    - [FeLS - Fetch Landsat & Sentinel Data from Google Cloud (1.4.0.1)](https://github.com/vascobnunes/fetchLandsatSentinelFromGoogleCloud.git/) repository in the folder :\
    `/Configs/fetchLandsatSentinelFromGoogleCloud-master`

    - [ACOLITE - generic atmospheric correction module (20221114.0)](https://github.com/acolite/acolite.git/) repository in the folder :\
    `/Configs/acolite-main`

- Get credentials for the followings data providers:

    -   [Copernicus Open Access Hub](https://scihub.copernicus.eu/dhus/#/home/)
    -   [Terrascope](https://sso.terrascope.be/auth/realms/terrascope/protocol/openid-connect/auth?client_id=terrascope-viewer&redirect_uri=https%3A%2F%2Fviewer.esa-worldcover.org%2Fworldcover%2F%3Flanguage%3Den%26bbox%3D-262.61718749999994%2C-79.6556678546481%2C262.61718749999994%2C79.65566785464813%26overlay%3Dfalse%26bgLayer%3DOSM%26date%3D2023-01-19%26layer%3DWORLDCOVER_2021_MAP&state=76f1db73-28b4-4e8b-8b41-21a995a5ee92&response_mode=fragment&response_type=code&scope=openid&nonce=1fa78ab3-bf00-4834-8213-f331e0046921)
    -   [NASA EarthData ](https://urs.earthdata.nasa.gov/home)

    and type them in the file `Configs/Environments/.env`

- Place your saved Machine Learning models in :\
    `Configs/MLmodels/YourModelFolder/YourModel.pkl` &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(for scikit-learn)\
    `Configs/MLmodels/YourModelFolder/YourModel.zip` &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(for Py-Torch)\
    `Configs/MLmodels/YourModelFolder/YourModel.jld2`&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(for Julia Language models)

## Settings and Usage

Open User Input file in `Configs/User_Inputs.py` and follow the descriptions to set up wanted workflow options, insert region of interest and sensing period, select download service, define masking and classification options. Execute the script `Classification_Workflow.py` to run the workflow.



### Example

To test the classification workflow we provide a random forest model based on [MARIDA](https://github.com/marine-debris/marine-debris.github.io) spectral signatures library and trained as described in [Kikaki et al., 2022](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0262247).
