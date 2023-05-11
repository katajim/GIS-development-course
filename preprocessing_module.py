from osgeo import gdal 
from osgeo import ogr 
import numpy as np
from shapely.geometry import Polygon
import geopandas as gpd


def create_poly(geo_coords:list):
    ''' Just for testing purposes'''
    ''' Takes list of tuples'''
    pol = Polygon(geo_coords)
    gdf = gpd.GeoDataFrame(geometry=[pol], crs='epsg:3067')
    gdf.to_file('test.shp')

def read_geotiff(filename,rtn=True):
    ''' Reads a geotiff file
        Input: filename = r'path\to\geotiff_file.tif',rtn= Whether both are returned or only one
        Output: Geotiff file as dataset object,data as an numpy array
    '''
    # Open input file from path
    ds = gdal.Open(filename)

    # Get array
    band = ds.GetRasterBand(1)
    arr = band.ReadAsArray()

    if rtn==True:
        return arr, ds
    else: 
        return arr

def write_geotiff(filename, arr, in_ds, rtn_object=True):
    ''' Creates a geotiff file and writes to it
        Input: filename = r'path\to\geotiff_file.tif', arr = Numpy array,
         in_ds = Gdal dataset, rtn_object = Bool       
        Output: if rtn_object == True --> returns gdal dataset
                else returns None, but writes data to geotiff based on input array
    '''
    # Test input arrays datatype and define it based on that
    if arr.dtype == np.float32:
        arr_type = gdal.GDT_Float32
    else:
        arr_type = gdal.GDT_Int32
    # Create geotiff with given dimensions
    driver = gdal.GetDriverByName("GTiff")
    out_ds = driver.Create(filename, arr.shape[1], arr.shape[0], 1, arr_type)

    # Get projection and geotransform information from input file
    out_ds.SetProjection(in_ds.GetProjection())
    out_ds.SetGeoTransform(in_ds.GetGeoTransform())
    band = out_ds.GetRasterBand(1)
    band.FlushCache()
    band.ComputeStatistics(False)

    # Returns filepath
    if rtn_object==True:
        return out_ds
    
    # Writes input data to outputfile
    else:
        band.WriteArray(arr)

def rasterize(in_vector,in_dem,out_fp):
    ''' Rasterizes given vector file to same resolution and extent as given raster file
        Input: in_vector = r'path\to\vector_file.shp', in_dem = r'path\to\geotiff_file.tif', out_fp = r'path\to\geotiff_file.tif'
        Output: out_fp parameter as a string
    '''
    # Open both raster and vector layers with gdal and ogr
    print('start rasterize')
    arr,ras_ds = read_geotiff(in_dem)
    vec_ds = ogr.Open(in_vector) 
    lyr = vec_ds.GetLayer()
    
    # Write an empty geotiff
    chn_ras_ds = write_geotiff(out_fp,arr,ras_ds)

    # Rasterize given vector file with same resolution as input dem 
    # Append to empty geotiff file 
    gdal.RasterizeLayer(chn_ras_ds, [1], lyr) 
    chn_ras_ds.GetRasterBand(1).SetNoDataValue(0.0) 
    
    # Close the file 
    chn_ras_ds= None

    print('end rasterize')
    # returns parameter out_fp 
    return out_fp

def pixel(file,dx,dy):
    ''' Finds geo coordinates from pixel coordinates
        Input: file = GDAL dataset, dx = pixel_x, dy = pixel_y  

    '''
    GT = file.GetGeoTransform()
    X_geo = GT[0] + dx * GT[1] + dy * GT[2]
    Y_geo = GT[3] + dx * GT[4] + dy * GT[5]
    return X_geo,Y_geo

def bounding_box(points, min_x=-np.inf, max_x=np.inf, min_y=-np.inf,
                        max_y=np.inf, min_z=-np.inf, max_z=np.inf):
    ''' Creates a bounding box based on given x,y,z information (base parameter to infinity)
        Input: points= numpy 2D array,min_x...max_z = bounding values as integer
        Output: bool numpy array
    
    '''
    # Calculate bounds 
    bound_x = np.logical_and(points[:,0] > min_x, points[:,0] < max_x)
    bound_y = np.logical_and(points[:,1] > min_y, points[:,1] < max_y)
    bound_z = np.logical_and(points[:,2] > min_z, points[:,2] < max_z)

    # Create filter based on bounds
    bb_filter = np.logical_and(np.logical_and(bound_x, bound_y), bound_z)

    return bb_filter
