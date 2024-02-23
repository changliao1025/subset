import sys
import time
from pathlib import Path
from os.path import realpath
import numpy as np
#this is the pre-processing of the data
#basically the input needs at least (1) boundary, (2) dem


sPath = '/qfs/people/liao313/workspace/python/subset/'
sys.path.append(sPath)

from subset.subset_raster import subset_raster

sFilename_raster_in = '/compyfs/icom/liao313/00raw/dem/hyd_ar_dem_15s/hyd_ar_dem_15s.tif'
sFilename_geojson_in = '/compyfs/liao313/04model/pyhexwatershed/sag/pyhexwatershed20240101001/pyflowline/mpas.geojson'

#example 1, call without saving the output
#time the process

tStart = time.time()
vData=subset_raster(sFilename_raster_in, sFilename_geojson_in)
tEnd = time.time()
print('Elapsed time is: ', tEnd - tStart)

#example 2, call and save the output in folder
sFolder_raster_out = '//compyfs/liao313/04model/subset/sag'
tStart = time.time()
subset_raster(sFilename_raster_in, sFilename_geojson_in, 1, sFolder_raster_out)
tEnd = time.time()
print('Elapsed time is: ', tEnd - tStart)

#calculate the elevation profile using result from example 1
nElevation_profile = 11
tStart = time.time()
for pData in vData:
    #create a 11 element numpy array to store the result 
    aElevation_profile = np.zeros(nElevation_profile)      
    #remove the missing value
    aData = pData[np.where(pData != -9999)]
    #call the numpy percentile function
    aElevation_profile[0] = np.min(aData)
    aElevation_profile[nElevation_profile-1] = np.max(aData)
    for i in range(1, nElevation_profile-1):
        aElevation_profile[i] = np.percentile(aData, i*10)

    #print(aElevation_profile)

tEnd = time.time()
print('Elapsed time is: ', tEnd - tStart)

