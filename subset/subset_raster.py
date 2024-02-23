import os, sys
import numpy as np
from osgeo import gdal, osr, ogr, gdalconst

from pyearth.toolbox.management.vector.reproject import reproject_vector
from pyearth.gis.gdal.read.raster.gdal_read_geotiff_file import gdal_read_geotiff_file

def subset_raster(sFilename_raster_in, sFilename_polygon_in, 
                  iFlag_save_in = None, 
                  sFolder_raster_out= None, 
                  sFormat_in='GTiff'):
    """
    Clip a raster by a shapefile
    :param sFilename_raster_in: input raster filename
    :param sFilename_polygon_in: input polygon filename
    :param sFilename_raster_out: output raster filename
    :param sFormat: output format
    :return: None
    """

    #check input files
    if os.path.exists(sFilename_raster_in):
        pass
    else:
        print('The raster file does not exist!')
        return
    
    if os.path.exists(sFilename_polygon_in):
        pass
    else:   
        print('The shapefile does not exist!')
        return
    
    #check the input raster data format and decide gdal driver
    if sFormat_in is not None:
        sDriverName = sFormat_in
    else: 
        sDriverName = 'GTiff'

    if iFlag_save_in is not None:
        iFlag_save = iFlag_save_in
    else:
        iFlag_save = 0

    if iFlag_save == 1:
        if sFolder_raster_out is not None:
            if os.path.exists(sFolder_raster_out):
                pass
            else:
                #create the folder
                os.makedirs(sFolder_raster_out)
                
        else:
            #save the output to the same folder as the input
            sFolder_raster_out = os.path.dirname(sFilename_raster_in)
    else:
        print('The output raster will not be saved unless there is only one polygon!')

    pDriver = gdal.GetDriverByName(sDriverName)
    pDriver_shapefile = ogr.GetDriverByName('ESRI Shapefile')
    sFilename_shapefile_cut = "/vsimem/tmp_polygon.shp"
    #get the raster file extension
    sExtension = os.path.splitext(sFilename_raster_in)[1]
    sName = os.path.basename(sFilename_raster_in)        
    sRasterName_no_extension = os.path.splitext(sName)[0]

    pDataset_data = gdal.Open(sFilename_raster_in, gdal.GA_ReadOnly)
   
    dummy = gdal_read_geotiff_file(sFilename_raster_in)
    aData= dummy['dataOut']
    eType = dummy['dataType']  
    dPixelWidth = dummy['pixelWidth']                        
    pPixelHeight = dummy['pixelHeight']
    dOriginX = dummy['originX']
    dOriginY = dummy['originY']
    nrow = dummy['nrow']
    ncolumn = dummy['ncolumn']
    dMissing_value= dummy['missingValue']
    pProjection = dummy['projection']
    pSpatialRef_target = dummy['spatialReference']
    wkt1 = pSpatialRef_target.ExportToWkt()
    dX_left=dOriginX
    dX_right = dOriginX + ncolumn * dPixelWidth
    dY_top = dOriginY
    dY_bot = dOriginY + nrow * pPixelHeight

    #get the spatial reference of the shapefile
    pDataset_subset = ogr.Open(sFilename_polygon_in)        
    pLayer = pDataset_subset.GetLayer(0)   
    # Count the number of features (polygons)
    nFeature = pLayer.GetFeatureCount()
    # Get the spatial reference of the layer
    pSpatialRef_source = pLayer.GetSpatialRef()
    wkt2 = pSpatialRef_source.ExportToWkt()    

    #check whether the polygon has only one or more features
    if nFeature > 1:
        pass        
    else:
        print('The polygon file has only one polygons!')
        return
      
    #check the polygon spatial reference, reporject if necessary
    if(wkt1 != wkt2):   
        pDataset_clip = None
        pLayer_clip = None     
        #in this case, we can reproject the shapefile to the same spatial reference as the raster
        #get the folder that contains the shapefile
        sFolder = os.path.dirname(sFilename_polygon_in)
        #get the name of the shapefile
        sName = os.path.basename(sFilename_polygon_in)
        #get the name of the shapefile without extension
        sName_no_extension = os.path.splitext(sName)[0]
        #create a new shapefile
        sFilename_clip_out = sFolder + '/' + sName_no_extension + '_transformed.shp'
        reproject_vector(sFilename_polygon_in, sFilename_clip_out, pSpatialRef_target)        
        #use the new shapefile to clip the raster
        sFilename_clip = sFilename_clip_out     
    else:
        sFilename_clip = sFilename_polygon_in
        #read the first polygon 
        
    #get the envelope of the polygon
    
    #now loop through all the polygons in the vector file
    pDataset_subset = ogr.Open(sFilename_clip)
    pLayer_subset = pDataset_subset.GetLayer(0) 
    aData_subset = list()
    if iFlag_save == 1:
        #all the clipped rasters will be saved to the output folder
        for i in range(nFeature):
            sClip = "{:03d}".format(i)
            sFilename_raster_out  = sFolder_raster_out + '/' + sRasterName_no_extension + '_clip_' + sClip + sExtension
            pFeature_subset = pLayer_subset.GetFeature(i)        
            pPolygon = pFeature_subset.GetGeometryRef()   
            #use the gdal warp function to clip the raster
            minX, maxX, minY, maxY = pPolygon.GetEnvelope()
            iNewWidth = int( (maxX - minX) / abs(dPixelWidth)  )
            iNewHeigh = int( (maxY - minY) / abs(dPixelWidth) )
            newGeoTransform = (minX, dPixelWidth, 0,    maxY, 0, -dPixelWidth)  
            if minX > dX_right or maxX < dX_left    or minY > dY_top or maxY < dY_bot:        
                #this polygon is out of bound            
                pass
            else:       
                #create the temporary shapefile
                pDataset3 = pDriver_shapefile.CreateDataSource(sFilename_shapefile_cut)
                pLayerOut3 = pDataset3.CreateLayer('cell', pSpatialRef_target, ogr.wkbPolygon)    
                pLayerDefn3 = pLayerOut3.GetLayerDefn()
                pFeatureOut3 = ogr.Feature(pLayerDefn3)
                pFeatureOut3.SetGeometry(pPolygon)  
                pLayerOut3.CreateFeature(pFeatureOut3)    
                pDataset3.FlushCache()

                pDataset_clip = pDriver.Create(sFilename_raster_out, iNewWidth, iNewHeigh, 1, eType)
                pDataset_clip.SetGeoTransform( newGeoTransform )
                pDataset_clip.SetProjection( pProjection)   
                pWrapOption = gdal.WarpOptions( cropToCutline=True,cutlineDSName = sFilename_shapefile_cut , \
                        width=iNewWidth,   \
                            height=iNewHeigh,      \
                                dstSRS=pProjection , format = sDriverName )
                pDataset_clip_warped = gdal.Warp(sFilename_raster_out, pDataset_data, options=pWrapOption)

                #convert the warped dataset to an array
                aData_clip = pDataset_clip_warped.ReadAsArray()
                #change the missing value to the original missing value
                aData_clip[aData_clip == dMissing_value] = -9999
                # Write the warped dataset to the output raster
                pDataset_clip.GetRasterBand(1).WriteArray(aData_clip)        
                #close the dataset
                pDataset_clip = None
                aData_subset.append(aData_clip)
                        
    else:
        #all the clipped raster will saved in the memory and a List will be returned
        sDriverName = 'MEM'
        pDriver_memory = gdal.GetDriverByName(sDriverName)
        
        
        
        for i in range(nFeature):
            pFeature_subset = pLayer_subset.GetFeature(i)        
            pPolygon = pFeature_subset.GetGeometryRef()   
            #use the gdal warp function to clip the raster
            minX, maxX, minY, maxY = pPolygon.GetEnvelope()
            iNewWidth = int( (maxX - minX) / abs(dPixelWidth)  )
            iNewHeigh = int( (maxY - minY) / abs(dPixelWidth) )      
            newGeoTransform = (minX, dPixelWidth, 0,    maxY, 0, -dPixelWidth)  
            if minX > dX_right or maxX < dX_left    or minY > dY_top or maxY < dY_bot:        
                #this polygon is out of bound            
                pass
            else:     
                #create the temporary shapefile
                pDataset3 = pDriver_shapefile.CreateDataSource(sFilename_shapefile_cut)
                pLayerOut3 = pDataset3.CreateLayer('cell', pSpatialRef_target, ogr.wkbPolygon)    
                pLayerDefn3 = pLayerOut3.GetLayerDefn()
                pFeatureOut3 = ogr.Feature(pLayerDefn3)
                pFeatureOut3.SetGeometry(pPolygon)  
                pLayerOut3.CreateFeature(pFeatureOut3)    
                pDataset3.FlushCache()

                pDataset_clip = pDriver_memory.Create('', iNewWidth, iNewHeigh, 1, eType)
                pDataset_clip.SetGeoTransform( newGeoTransform )
                pDataset_clip.SetProjection( pProjection)   
                pWrapOption = gdal.WarpOptions( cropToCutline=True,cutlineDSName = sFilename_shapefile_cut , 
                        width=iNewWidth,   
                            height=iNewHeigh,      
                                dstSRS=pProjection , format = sDriverName )
                pDataset_clip_warped = gdal.Warp('', pDataset_data, options=pWrapOption)
                #convert the warped dataset to an array
                aData_clip = pDataset_clip_warped.ReadAsArray()
                #change the missing value to the original missing value
                aData_clip[aData_clip == dMissing_value] = -9999
                # Write the warped dataset to the output raster
                
                pDataset3 = None
                pLayerOut3 = None
                pDataset_clip = None
                #close the dataset            
                aData_subset.append(aData_clip)

    #return the clipped raster list
    return aData_subset