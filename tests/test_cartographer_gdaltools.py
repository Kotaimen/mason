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


def load_raster_file(filename, data_format):
    with open(filename, 'rb') as fp:
        test_data = fp.read()
    return gdaltools.GDALRaster(test_data, data_format)


def save_raster_file(filename, raster):
    with open(filename, 'wb') as fp:
        fp.write(raster.data)


class TestHillShading(unittest.TestCase):

    def setUp(self):
        self._input_filename = './input/hailey.tiff'
        self._output_filename = './output/test_hailey_hillshading.tif'
        self._data_format = Format.GTIFF

    def testHillShading(self):
        test_raster = load_raster_file(self._input_filename, self._data_format)
        processor = gdaltools.GDALHillShading(zfactor=2,
                                              scale=111120,
                                              altitude=45,
                                              azimuth=315,
                                              )
        hillshading = processor.convert(test_raster)
        save_raster_file(self._output_filename, hillshading)


class TestColorRelief(unittest.TestCase):

    def setUp(self):
        self._input_filename = './input/hailey.tiff'
        self._output_filename = './output/test_hailey_colorrelief.tif'
        self._color_context = './input/hypsometric-map-world.txt'
        self._data_format = Format.GTIFF

    def testColorRelief(self):
        test_raster = load_raster_file(self._input_filename, self._data_format)
        processor = gdaltools.GDALColorRelief(self._color_context)
        colorrelief = processor.convert(test_raster)
        save_raster_file(self._output_filename, colorrelief)


class TestWarp(unittest.TestCase):

    def setUp(self):
        self._input_filename = './input/hailey.tiff'
        self._output_filename = './output/test_hailey_warp.tif'
        self._data_format = Format.GTIFF

    def testWarp(self):
        test_raster = load_raster_file(self._input_filename, self._data_format)
        processor = gdaltools.GDALWarper(dst_epsg=3857)
        warp = processor.convert(test_raster)
        save_raster_file(self._output_filename, warp)


class TestMetaData(unittest.TestCase):

    def setUp(self):
        self._input_filename = './input/hailey.tiff'
        self._output_filename = './output/test_hailey_metadata.tif'
        self._data_format = Format.GTIFF

    def testMetaData(self):
        test_raster = load_raster_file(self._input_filename, self._data_format)
        set_srs = 4326
        set_envelope = (-180, -90, 180, 90)
        set_nodata = -32768
        processor = gdaltools.GDALRasterMetaData(to_srs=set_srs,
                                                 to_envelope=set_envelope,
                                                 to_tiled=False,
                                                 to_compressed=False,
                                                 nodata=set_nodata,
                                                 )
        metadata = processor.convert(test_raster)
        save_raster_file(self._output_filename, metadata)


class TestToPNG(unittest.TestCase):

    def setUp(self):
        self._input_filename = './output/test_hailey_colorrelief.tif'
        self._output_filename = './output/test_hailey_png.png'
        self._data_format = Format.GTIFF

    def testToPNG(self):
        test_raster = load_raster_file(self._input_filename, self._data_format)
        processor = gdaltools.GDALRasterToPNG()
        png = processor.convert(test_raster)
        save_raster_file(self._output_filename, png)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
