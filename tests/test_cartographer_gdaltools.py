# -*- coding:utf-8 -*- 
'''
UnitTest for GDALtools

Created on Aug 31, 2012
@author: ray
'''


import unittest

from mason.core import Format
from mason.cartographer import gdaltools


class TestSpatialReference(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_forward(self):
        place = 12
        c = gdaltools.SpatialReference(4326, 3857, place=place)

        x1, y1, z1 = (0.0, 0.0, 0.0)
        x2, y2, z2 = c.forward(x1, y1, z1)
        self.assertAlmostEqual(x2, 0.0, place)
        self.assertAlmostEqual(y2, -7.081154551613622e-10, place)
        self.assertAlmostEqual(z2, 0.0, place)

        x3, y3, z3 = c.reverse(*c.forward(x1, y1, z1))
        self.assertAlmostEqual(x3, x1, place)
        self.assertAlmostEqual(y3, y1, place)
        self.assertAlmostEqual(z3, z1, place)

        x1, y1, z1 = (-180.0, 0.0, 0.0)
        x2, y2, z2 = c.forward(x1, y1, z1)
        self.assertAlmostEqual(x2, -20037508.342789248, place)
        self.assertAlmostEqual(y2, -7.081154551613622e-10, place)
        self.assertAlmostEqual(z2, 0.0, place)

        x3, y3, z3 = c.reverse(*c.forward(x1, y1, z1))
        self.assertAlmostEqual(x3, x1, place)
        self.assertAlmostEqual(y3, y1, place)
        self.assertAlmostEqual(z3, z1, place)

    def test_reverse(self):
        place = 12
        c = gdaltools.SpatialReference(4326, 3857, place=place)

        x1, y1, z1 = (0.0, -7.081154551613622e-10, 0.0)
        x2, y2, z2 = c.reverse(x1, y1, z1)
        self.assertAlmostEqual(x2, 0.0, place)
        self.assertAlmostEqual(y2, 0.0, place)
        self.assertAlmostEqual(z2, 0.0, place)

        x3, y3, z3 = c.forward(*c.reverse(x1, y1, z1))
        self.assertAlmostEqual(x3, x1, place)
        self.assertAlmostEqual(y3, y1, place)
        self.assertAlmostEqual(z3, z1, place)

        x1, y1, z1 = (-20037508.342789248, -7.081154551613622e-10, 0.0)
        x2, y2, z2 = c.reverse(x1, y1, z1)
        self.assertAlmostEqual(x2, -180.0, place)
        self.assertAlmostEqual(y2, 0.0, place)
        self.assertAlmostEqual(z2, 0.0, place)

        x3, y3, z3 = c.forward(*c.reverse(x1, y1, z1))
        self.assertAlmostEqual(x3, x1, place)
        self.assertAlmostEqual(y3, y1, place)
        self.assertAlmostEqual(z3, z1, place)


class TestGDALProcess(unittest.TestCase):

    def setUp(self):
        test_filename = './input/hailey.tiff'
        with open(test_filename, 'rb') as fp:
            test_data = fp.read()

        test_format = Format.GTIFF

        self._test_raster = gdaltools.GDALRaster(test_data, test_format)

    def tearDown(self):
        pass

    def test_hillshade(self):
        hillshading = gdaltools.GDALHillShading(zfactor=2,
                                                scale=111120,
                                                altitude=45,
                                                azimuth=315,
                                                )
        hillshading.convert(self._test_raster)

    def test_colorrelief(self):
        color_context = './input/hypsometric-map-world.txt'
        colorrelief = gdaltools.GDALColorRelief(color_context)
        colorrelief.convert(self._test_raster)

    def test_warp(self):
        warper = gdaltools.GDALWarper(src_epsg=4267, dst_epsg=3857)
        warper.convert(self._test_raster)

    def test_metadata(self):
        meta_convertor = gdaltools.GDALRasterMetaData(to_srs=4326,
                                                      to_envelope=(-180, -90, 180, 90),
                                                      to_tiled=False,
                                                      to_compressed=False,
                                                      nodata= -32768,
                                                     )
        meta_convertor.convert(self._test_raster)

    def test_to_png(self):
        png_convertor = gdaltools.GDALRasterToPNG()
        png_convertor.convert(self._test_raster)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
