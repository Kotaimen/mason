'''
Created on May 2, 2012

@author: ray
'''
import os
import unittest
from mason.cartographer.gdalutil import (gdal_hillshade,
                                         gdal_colorrelief,
                                         gdal_warp)


class GDALHillShadeTest(unittest.TestCase):

    def setUp(self):
        self._test_dem = './input/hailey.tiff'

    def tearDown(self):
        pass

    def test_HillFront(self):
        test_source = self._test_dem
        test_result = './output/test_hillfront.tif'
        if os.path.exists(test_result):
            os.remove(test_result)

        ret = gdal_hillshade(test_source,
                             test_result,
                             zfactor=2,
                             scale=111120,
                             azimuth=315,
                             altitude=45)
        self.assert_(ret)

    def test_HillShadow(self):
        test_source = self._test_dem
        test_result = './output/test_hillshadow.tif'
        if os.path.exists(test_result):
            os.remove(test_result)

        ret = gdal_hillshade(test_source,
                             test_result,
                             zfactor=2,
                             scale=111120,
                             azimuth=135,
                             altitude=75)
        self.assert_(ret)

    def test_PNG(self):
        test_source = self._test_dem
        test_result = './output/test_hillshade_png.png'
        if os.path.exists(test_result):
            os.remove(test_result)

        ret = gdal_hillshade(test_source,
                             test_result,
                             zfactor=2,
                             scale=111120,
                             azimuth=315,
                             altitude=45,
                             image_type='PNG')
        self.assert_(ret)

    def test_JPEG_10(self):
        test_source = self._test_dem
        test_result = './output/test_hillshade_jpeg_10.jpg'
        if os.path.exists(test_result):
            os.remove(test_result)

        ret = gdal_hillshade(test_source,
                             test_result,
                             zfactor=2,
                             scale=111120,
                             azimuth=315,
                             altitude=45,
                             image_type='JPEG',
                             image_parameters={'quality': 10})
        self.assert_(ret)

    def test_JPEG_95(self):
        test_source = self._test_dem
        test_result = './output/test_hillshade_jpeg_95.jpg'
        if os.path.exists(test_result):
            os.remove(test_result)

        ret = gdal_hillshade(test_source,
                             test_result,
                             zfactor=2,
                             scale=111120,
                             azimuth=315,
                             altitude=45,
                             image_type='JPEG',
                             image_parameters={'quality': 95})
        self.assert_(ret)


class GDALColorReliefTest(unittest.TestCase):

    def setUp(self):
        self._test_dem = './input/hailey.tiff'
        self._test_color_context = './input/HypsometricColors(Dark).txt'

    def tearDown(self):
        pass

    def test_ColorRelief(self):
        test_source = self._test_dem
        test_result = './output/test_color_relief.tif'
        test_color = self._test_color_context

        if os.path.exists(test_result):
            os.remove(test_result)

        ret = gdal_colorrelief(test_source,
                               test_result,
                               test_color)
        self.assert_(ret)

    def test_PNG(self):
        test_source = self._test_dem
        test_result = './output/test_color_relief_png.png'
        test_color = self._test_color_context

        if os.path.exists(test_result):
            os.remove(test_result)

        ret = gdal_colorrelief(test_source,
                               test_result,
                               test_color,
                               image_type='PNG')
        self.assert_(ret)

    def test_JPEG_10(self):
        test_source = self._test_dem
        test_result = './output/test_color_relief_jpeg_10.jpg'
        test_color = self._test_color_context

        if os.path.exists(test_result):
            os.remove(test_result)

        ret = gdal_colorrelief(test_source,
                               test_result,
                               test_color,
                               image_type='JPEG',
                               image_parameters={'quality': 10}
                               )
        self.assert_(ret)

    def test_JPEG_95(self):
        test_source = self._test_dem
        test_result = './output/test_color_relief_jpeg_95.jpg'
        test_color = self._test_color_context

        if os.path.exists(test_result):
            os.remove(test_result)

        ret = gdal_colorrelief(test_source,
                               test_result,
                               test_color,
                               image_type='JPEG',
                               image_parameters={'quality': 95}
                               )
        self.assert_(ret)


class GDALWarp(unittest.TestCase):

    def setUp(self):
        self._test_dem = './input/hailey.tiff'

    def test_WarpTo256x256(self):
        test_source = self._test_dem
        test_result = './output/test_warp.tif'

        if os.path.exists(test_result):
            os.remove(test_result)

        ret = gdal_warp(test_source, test_result, 256, 256)
        self.assert_(ret)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
