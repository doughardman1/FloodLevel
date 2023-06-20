# FloodLevel
Terrain processing and flood level in python

Takes some LiDAR rasters and performs some geoprocessing on them and then applies a flood fill algorithm to a point at a chosen elevation and plots resulting flood extents

Me attempting to learn GDAL and osgeo

## To get it running on my ubuntu system
- install miniconda
- create a conda env to install gdal in
- activate gdal env
- install gdal with conda-forge
```
conda create -n gdal
conda activate gdal
conda install -c conda-forge gdal
```
Everything else works fine just installing with pip
