import glob

from osgeo import gdal
from osgeo import gdalconst 

import cartopy.crs as ccrs

import numpy as np
import matplotlib.pyplot as plt

import pandas as pd
import geopandas as gpd


def prepareLiDAR(filepath):
    '''
    takes a (relative in this case) filepath and saves a virtual raster of the LiDAR (.tif) files saved in the folder,
    Returns an np array of band 1 (elevations) and the gdal.geotransform of the raster
    '''

    # read terrain50 tiles, generate vrt, convert to tif
    incoming_su = glob.glob(filepath + 'su/' + '*.asc')
    incoming_tq = glob.glob(filepath + 'tq/' + '*.asc')
    vrt = gdal.BuildVRT('su.vrt', incoming_su)
    vrt = gdal.BuildVRT('tq.vrt', incoming_tq)

    vrt.FlushCache()

    # create warp options object and warp vrt so generate geotiff
    options = gdal.WarpOptions(format='GTiff', dstSRS='EPSG:27700')
    #mergedTiff = gdal.Warp('LiDAR.tif','LiDAR.vrt', options=options)
    #mergedTiff.FlushCache()

    # save band 1 (LiDAR elevations) as np array
    elevations = vrt.GetRasterBand(1).ReadAsArray()
    
    #geotransform: [xMin (west), xCellSize, xRotation, yMax (north), yCellSize, yRotation]
    geotransform = vrt.GetGeoTransform()  

    return (elevations, geotransform)

def readRaster(filename):
    """
    Uses a gdal to read DTM
    Returns dataset, elevations, and geotransform
    """
    # Use gdal to read the DEM file
    dataset = gdal.Open(filename)

    # save band 1 (LiDAR elevations) as np array
    elevations = dataset.GetRasterBand(1).ReadAsArray()
    
    #geotransform: [xMin (west), xCellSize, xRotation, yMax (north), yCellSize, yRotation]
    geotransform = dataset.GetGeoTransform()

    return (dataset, elevations, geotransform)


def calculateXY(elevations, geotransform):
    '''
    returns pixel data in northings (m) and eastings (m)
    '''
    
    xCellSize = geotransform[1] # x-axis LiDAR resolution
    yCellSize = geotransform[5] # y-axis LiDAR resolution (note this returns negative as it reads raster from top left corner)
    
    # co-ordinates of center of minimum pixel (south-west / bottom left)
    xMin = geotransform[0] + xCellSize * 0.5 
    yMin = geotransform[3] + (yCellSize * elevations.shape[1]) - yCellSize * 0.5

    # co-ordinates of center of maximum pixel (north-east / top right)
    xMax = geotransform[0] + (xCellSize * elevations.shape[0]) - xCellSize * 0.5
    yMax = geotransform[3] + yCellSize * 0.5

    xCenter=(xMin+xMax)/2
    yCenter=(yMin+yMax)/2 
    
    return (xCellSize, yCellSize, xMin, yMin, xMax, yMax, xCenter, yCenter)


def transverseMercatorPlot(elevations, geotransform):
    '''
    flips LiDAR elevation data from readRaster() function so that it indexes in the same way that the transverse mercator co-ordinates do,
    returns np array that  reads in the same way as the co-ordinates, ie. [0, 0] is now bottom left pixel
    '''
    
    xres, yres, xmin, ymin, xmax, ymax, x_center, y_center = calculateXY(elevations, geotransform)
    
    flippedElevations = np.flipud(elevations) # since the plotting happens row-wise from bottom to top, the array needs to be flipped 

    projection = ccrs.OSGB() 

    return flippedElevations

def getPixelLocationInArray(geotransform, xCoordinate, yCoordinate):
    """
    Uses a gdal geomatrix (gdal.GetGeoTransform()) to calculate
    the pixel location of a geospatial coordinate 
    """
    xCellSize = geotransform[1] #size of cell along x axis
    yCellSize = geotransform[5] #size of cell along y axis

    x = geotransform[0]
    y = geotransform[3]

    pixel = int((xCoordinate - x) / xCellSize)

    row = int((y - yCoordinate) / yCellSize)
    
    return (abs(pixel), abs(row))
    # this needs to be tested on a raster tile that is not a square - Doug to merge two LiDAR tiles together to do this
    # does npArray indexing start from 0 or 1?



def plotMap(nparray, title):
    fig = plt.figure(figsize=(6, 3.2))
    ax = fig.add_subplot()
    ax.set_title(title)
    plt.imshow(nparray)
    plt.show()


def floodFill(col, row, mask):
    filled = set()

    fill = set()
    fill.add((col, row))
    width = mask.shape[1]-1
    height = mask.shape[0]-1

    flood = np.zeros_like(mask, dtype=np.int8)

    while fill:
        x,y = fill.pop()
        
        if y == height or x == width or x < 0 or y < 0:
            continue

        if mask[y][x] == 1:
            # Do fill
            flood[y][x]=1
            filled.add((x,y))
            # Check neighbors for 1 values
            west =(x-1,y)
            east = (x+1,y)
            north = (x,y-1)
            south = (x,y+1)
            if not west in filled:
                fill.add(west)
            if not east in filled:
                fill.add(east)
            if not north in filled:
                fill.add(north)
            if not south in filled:
                fill.add(south)
            
    return flood

if __name__ == "__main__":

    # read lidar, save vrt of tiles, save tif clipped to shapefile, return elevtions and geo transform
    #filepath = '/Users/Doug/Documents/Programming Exercises/DEMProcessing/terr50_gagg_gb/data/'
    #prepareLiDAR(filepath)
    
    topography = readRaster('/Users/Doug/Documents/Programming Exercises/DEMProcessing/Catchment/OS_terrain50_clipped_to_100m_buffered_catchment.tif')

    map = transverseMercatorPlot(topography[1], topography[2]) # np array of correctly oriented lidar elevaions

    flood_fill_70 = np.where(map < 70, 1,0)
    x, y = getPixelLocationInArray(topography[2],500105,146605)
    print(x,y)
    fldModel = floodFill(x,y, flood_fill_70)

    fldModel = transverseMercatorPlot(fldModel,topography[2])
    plotMap(fldModel, '70m')
 
