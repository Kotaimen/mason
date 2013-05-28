# -*- coding:utf-8 -*-
'''
UnitTest for GDALtools

Created on Aug 31, 2012
@author: ray
'''


import unittest

from mason.core import Format
from mason.utils import SpatialTransformer, gdal_hillshading, gdal_colorrelief


class TestSpatialReference(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_forward(self):
        place = 12
        c = SpatialTransformer(4326, 3857, place=place)

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
        c = SpatialTransformer(4326, 3857, place=place)

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


class TestHillShading(unittest.TestCase):

    def setUp(self):
        self._src = './input/hailey.tif'
        self._dst = './output/test_gdal_hillshading.tif'

    def testHillShading(self):
        gdal_hillshading(self._src, self._dst,
                         zfactor=2,
                         scale=111120,
                         altitude=45,
                         azimuth=315,
                         )


class TestColorRelief(unittest.TestCase):

    def setUp(self):
        self._src = './input/hailey.tif'
        self._dst = './output/test_gdal_colorrelief.tif'
        self._color_context = './input/hypsometric-map-world.txt'

    def testColorRelief(self):
        gdal_colorrelief(self._src, self._dst, self._color_context)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
