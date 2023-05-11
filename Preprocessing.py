from preprocessing_module import * 
import laspy
import time
##Parameters##
in_vec = r"C:\Users\Matti Katajisto\OneDrive - Aalto University\GIS-4030 GIS-development\Repo\GIS-development-course\test_data\Test_area_buildings.shp"
in_dem = r"C:\Users\Matti Katajisto\OneDrive - Aalto University\GIS-4030 GIS-development\Repo\GIS-development-course\test_data\Test_area_dem.tif"
out_fp_buildings = r"C:\Users\Matti Katajisto\OneDrive - Aalto University\GIS-4030 GIS-development\Repo\GIS-development-course\test_data\output\rasterized_buildings.tif"
classification = 5
laz_file = r"C:\Users\Matti Katajisto\OneDrive - Aalto University\GIS-4030 GIS-development\Repo\GIS-development-course\test_data\Test_area_laser.laz"
out_fp_dem_w_buildings = r"C:\Users\Matti Katajisto\OneDrive - Aalto University\GIS-4030 GIS-development\Repo\GIS-development-course\test_data\output\Dem_w_buildings"

##Processing##
start = time.time()

raster_buildings = rasterize(in_vec,in_dem,out_fp_buildings)
with laspy.open(laz_file) as laz:
    # Decompress laz to las file
    # Read raster file as npArray
    las_file = laz.read()
    raster_arr,dataset = read_geotiff(raster_buildings)
    raster_dem = read_geotiff(in_dem,False)
    # Test if the count of uncompressed data is the same as compressed
    # -> NO data lost on decompression
    if  laz.header.point_count != len(las_file.points):
        raise ValueError (f'Points from laz header count({laz.header.point_count}) and points from data count({len(las_file.points)}) do not match')

    # Get only points that have given classification 
    las_file.points = las_file.points[las_file.classification == classification]
    
    for row in range(raster_arr.shape[0]):
        for col in range(raster_arr.shape[1]):
            #Check if the pixel value is 255 (Meaning that it is a building pixel)
            pixel_value = raster_arr[row,col]
            if pixel_value != 255:
                continue
            print(f'Working on building pixel at [row:{row},col:{col}]')

            # Transform pixel coordinates to geo coordinates
            pixel_coords = [(col, row), (col + 1, row), (col + 1, row + 1), (col, row + 1)]
            geo_coords = []
            for coord in pixel_coords:
                x_y = pixel(dataset,coord[0],coord[1])
                geo_coords.append(x_y)
            
            # Get min and max coordinates to create a bounding box
            max_x = (max([coord[0] for coord in geo_coords]))
            max_y = (max([coord[1] for coord in geo_coords]))
            min_x = (min([coord[0] for coord in geo_coords]))
            min_y = (min([coord[1] for coord in geo_coords]))
            
            inside_box = bounding_box(las_file.xyz, min_x=min_x, max_x=max_x, min_y=min_y, max_y=max_y)
            p_inside_b = las_file.xyz[inside_box]
            
            # If there are points within the bounding box
            # Calculate average and append the value to raster_arr
            if len(p_inside_b)>0:
                average_height = sum([z[2] for z in p_inside_b])/len(p_inside_b)
                raster_dem[row,col] = average_height
            
# Write to Geotiff and close the LAS file
write_geotiff(out_fp_dem_w_buildings, raster_dem, dataset, False)
raster_buildings = None
laz.close()
end = time.time()
print(f'Processing time: {end-start}')

