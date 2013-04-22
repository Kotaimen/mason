# -*- coding:utf-8 -*-
'''
test_cartographer_raster

Created on Apr 11, 2013
@author: ray
'''
import unittest
import numpy
import math
import Image
from scipy import ndimage
from scipy import misc
from mason.cartographer.relief import GeoRaster, find_data
from osgeo import gdal, gdalconst, osr


class TestRasterData(unittest.TestCase):

    def test_fromfile(self):
        filename = '/mnt/geodata/DEM-Tools-patch/source/ned100m/n47w123.tif'
        raster = GeoRaster.from_file(filename)
        raster.summary()

        data = raster.read()
        print data.max(), data.min(), data.mean()

        aspect, slope = raster.aspect_and_slope(1, 111120)
        hillshade = raster.hillshade(aspect, slope, 315, 45)
        hillshade = (255 * hillshade).astype(numpy.ubyte)

        misc.imsave('/tmp/hillshade_1.png', hillshade)

        raster.close()

    def test_mosaic(self):

        srid = 'EPSG:4326'
        # minx, resx, skewx, maxy, skewy, resy
#        georeference = (-123.005556,
#                        0.0000926,
#                        0,ShadeRelief
#                        47.005556,
#                        0,
#                        - 0.0000926)

        georeference = (-122.000555555600002,
                        0.000926,
                        0,
                        47.000555555555515,
                        0,
                        - 0.000926)

        size = 1092, 1092
        raster = GeoRaster(srid, georeference, size)

#        dirpath = '/mnt/geodata/SRTM_30_org/world_org'
        dirpath = '/mnt/geodata/DEM-Tools-patch/source/ned10m/'
        minx, miny, maxx, maxy = raster.envelope

        for filename in find_data(dirpath, minx, miny, maxx, maxy):
            print filename
            raster.mosaic(filename)

        data = raster.read()
        print data.max(), data.min(), data.mean()

        aspect, slope = raster.aspect_and_slope(1, 111120)
        hillshade = raster.hillshade(aspect, slope, 315, 45)
        hillshade = (255 * hillshade).astype(numpy.ubyte)

        misc.imsave('/tmp/hillshade_2.png', hillshade)

        raster.close()

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()



