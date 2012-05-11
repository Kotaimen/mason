'''
Created on May 2, 2012

@author: ray
'''
import os
import unittest
from mason.cartographer.gdalutil import (gdal_hillshade,
                                         gdal_colorrelief,
                                         gdal_warp)


class GDALTest(unittest.TestCase):

    def setUp(self):
        self._test_dem = './input/hailey.tiff'
        self._test_color_context = './input/HypsometricColors(Dark).txt'

        self._test_hillshade1 = './output/test_hillshade1.tif'
        self._test_hillshade2 = './output/test_hillshade2.tif'
        self._test_colorrelief = './output/test_colorrelief.tif'
        self._test_warp = './output/test_warp.tif'

    def testHillShade(self):
        if os.path.exists(self._test_hillshade1):
            os.remove(self._test_hillshade1)
        if os.path.exists(self._test_hillshade2):
            os.remove(self._test_hillshade2)

        ret = gdal_hillshade(self._test_dem,
                             self._test_hillshade1,
                             zfactor=2,
                             scale=111120,
                             azimuth=315,
                             altitude=45,)
        self.assert_(ret)

        ret = gdal_hillshade(self._test_dem,
                             self._test_hillshade2,
                             zfactor=2,
                             scale=111120,
                             azimuth=135,
                             altitude=75)
        self.assert_(ret)

    def testColorRelief(self):
        if os.path.exists(self._test_colorrelief):
            os.remove(self._test_colorrelief)

        ret = gdal_colorrelief(self._test_dem,
                               self._test_colorrelief,
                               self._test_color_context)
        self.assert_(ret)

    def testWarp(self):
        if os.path.exists(self._test_warp):
            os.remove(self._test_warp)

        ret = gdal_warp(self._test_dem, self._test_warp, 256, 256)
        self.assert_(ret)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
