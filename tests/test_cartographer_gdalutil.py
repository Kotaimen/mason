'''
Created on May 2, 2012

@author: ray
'''
import os
import unittest
from mason.utils.gdalutil import (gdal_hillshade,
                                  gdal_colorrelief,
                                  gdal_warp)


class GDALHillShadeTest(unittest.TestCase):

    def setUp(self):
        test_dem = './input/hailey.tiff'
        with open(test_dem, 'rb') as fp:
            self._dem_data = fp.read()

    def tearDown(self):
        pass

    def _save_to_file(self, data, filename):
        if os.path.exists(filename):
            os.remove(filename)
        with open(filename, 'wb') as fp:
            fp.write(data)

    def test_HillFront(self):
        hillshade = gdal_hillshade(self._dem_data,
                                   zfactor=2,
                                   scale=111120,
                                   azimuth=315,
                                   altitude=45)

        self._save_to_file(hillshade, './output/test_hillfront.tif')

    def test_HillShadow(self):
        hillshade = gdal_hillshade(self._dem_data,
                                   zfactor=2,
                                   scale=111120,
                                   azimuth=135,
                                   altitude=75)

        self._save_to_file(hillshade, './output/test_hillshadow.tif')

    def test_PNG(self):
        hillshade = gdal_hillshade(self._dem_data,
                                   zfactor=2,
                                   scale=111120,
                                   azimuth=315,
                                   altitude=45,
                                   image_type='PNG')

        self._save_to_file(hillshade, './output/test_hillshade_png.png')

    def test_JPEG_10(self):
        hillshade = gdal_hillshade(self._dem_data,
                                     zfactor=2,
                                     scale=111120,
                                     azimuth=315,
                                     altitude=45,
                                     image_type='JPEG',
                                     image_parameters={'quality': 10})

        self._save_to_file(hillshade, './output/test_hillshade_jpeg_10.jpg')

    def test_JPEG_95(self):
        hillshade = gdal_hillshade(self._dem_data,
                                     zfactor=2,
                                     scale=111120,
                                     azimuth=315,
                                     altitude=45,
                                     image_type='JPEG',
                                     image_parameters={'quality': 95})

        self._save_to_file(hillshade, './output/test_hillshade_jpeg_95.jpg')


class GDALColorReliefTest(unittest.TestCase):

    def setUp(self):
        test_dem = './input/hailey.tiff'
        with open(test_dem, 'rb') as fp:
            self._dem_data = fp.read()
        self._color_context = './input/HypsometricColors(Dark).txt'

    def tearDown(self):
        pass

    def _save_to_file(self, data, filename):
        if os.path.exists(filename):
            os.remove(filename)
        with open(filename, 'wb') as fp:
            fp.write(data)

    def test_ColorRelief(self):
        test_source = self._dem_data
        test_result = './output/test_color_relief.tif'
        test_color = self._color_context

        color_relief = gdal_colorrelief(test_source, test_color)
        self._save_to_file(color_relief, test_result)

    def test_PNG(self):
        test_source = self._dem_data
        test_result = './output/test_color_relief_png.png'
        test_color = self._color_context

        color_relief = gdal_colorrelief(test_source,
                                        test_color,
                                        image_type='PNG',
                                        )
        self._save_to_file(color_relief, test_result)

    def test_JPEG_10(self):
        test_source = self._dem_data
        test_result = './output/test_color_relief_jpeg_10.jpg'
        test_color = self._color_context

        color_relief = gdal_colorrelief(test_source,
                                        test_color,
                                        image_type='JPEG',
                                        image_parameters={'quality': 10}
                                        )
        self._save_to_file(color_relief, test_result)

    def test_JPEG_95(self):
        test_source = self._dem_data
        test_result = './output/test_color_relief_jpeg_95.jpg'
        test_color = self._color_context

        color_relief = gdal_colorrelief(test_source,
                                        test_color,
                                        image_type='JPEG',
                                        image_parameters={'quality': 95}
                                        )
        self._save_to_file(color_relief, test_result)


class GDALWarp(unittest.TestCase):

    def setUp(self):
        test_dem = './input/hailey.tiff'
        with open(test_dem, 'rb') as fp:
            self._dem_data = fp.read()

    def _save_to_file(self, data, filename):
        if os.path.exists(filename):
            os.remove(filename)
        with open(filename, 'wb') as fp:
            fp.write(data)

    def test_WarpTo256x256(self):
        test_source = self._dem_data
        test_result = './output/test_warp_size.tif'

        warped = gdal_warp(test_source, size=(256, 256))
        self._save_to_file(warped, test_result)

    def test_WarpToGoogleMercator(self):
        test_source = self._dem_data
        test_result = './output/test_warp_proj.tif'

        warped = gdal_warp(test_source, srs=('EPSG:4326', 'EPSG:3857'))
        self._save_to_file(warped, test_result)

    def test_WarpToEnvelop(self):
        test_source = self._dem_data
        test_result = './output/test_warp_envelopwarpede.tif'

        warped = gdal_warp(test_source, envelope=(-114, 43, -113, 44))
        self._save_to_file(warped, test_result)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
