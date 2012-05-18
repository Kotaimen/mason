'''
Created on May 2, 2012

@author: ray
'''

import os
import unittest
from mason.cartographer.gdaldem import GDALHillShade, GDALColorRelief


TEST_SVR = 'postgresql+psycopg2://postgres:123456@localhost:5432/world_dem'
TEST_TBL = 'world'
TEST_ENVELOPE = (103.9995833, 27.9995833, 104.5004167, 28.5004167)


class CartographerHillShadeTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_HillShade_256x256(self):
        cartograher = GDALHillShade(server=TEST_SVR, dem_table=TEST_TBL)
        test_result = './output/test_cartographer_hillshade_256x256.tif'
        if os.path.exists(test_result):
            os.remove(test_result)

        size = (256, 256)
        envelope = TEST_ENVELOPE
        data = cartograher.doodle(envelope, size)
        self.assert_(data)

        with open(test_result, 'wb') as fp:
            fp.write(data)

        cartograher.close()

    def test_HillShade_512x512(self):
        cartograher = GDALHillShade(server=TEST_SVR, dem_table=TEST_TBL)
        test_result = './output/test_cartographer_hillshade_512x512.tif'
        if os.path.exists(test_result):
            os.remove(test_result)

        size = (512, 512)
        envelope = TEST_ENVELOPE
        data = cartograher.doodle(envelope, size)
        self.assert_(data)

        with open(test_result, 'wb') as fp:
            fp.write(data)

        cartograher.close()

    def test_HillShade_PNG(self):
        cartograher = GDALHillShade(server=TEST_SVR,
                                    dem_table=TEST_TBL,
                                    image_type='png')
        test_result = './output/test_cartographer_hillshade_png.png'
        if os.path.exists(test_result):
            os.remove(test_result)

        size = (256, 256)
        envelope = TEST_ENVELOPE
        data = cartograher.doodle(envelope, size)
        self.assert_(data)

        with open(test_result, 'wb') as fp:
            fp.write(data)

        cartograher.close()

    def test_HillShade_JPEG(self):
        cartograher = GDALHillShade(server=TEST_SVR,
                                    dem_table=TEST_TBL,
                                    image_type='jpeg',
                                    image_parameters={'quality': 95})
        test_result = './output/test_cartographer_hillshade_jpeg_95.jpg'
        if os.path.exists(test_result):
            os.remove(test_result)

        size = (256, 256)
        envelope = TEST_ENVELOPE
        data = cartograher.doodle(envelope, size)
        self.assert_(data)

        with open(test_result, 'wb') as fp:
            fp.write(data)

        cartograher.close()


class GDALColorReliefTest(unittest.TestCase):

    def setUp(self):
        self._color_context = './input/HypsometricColors(Light).txt'

    def test_ColorRelief_256x256(self):
        color_context = self._color_context
        cartograher = GDALColorRelief(color_context=color_context,
                                      server=TEST_SVR,
                                      dem_table='world',
                                      image_type='gtiff')

        test_result = './output/test_cartographer_colorrelief_256x256.tif'
        if os.path.exists(test_result):
            os.remove(test_result)

        size = (256, 256)
        envelope = TEST_ENVELOPE
        data = cartograher.doodle(envelope, size)
        self.assert_(data)

        with open(test_result, 'wb') as fp:
            fp.write(data)

        cartograher.close()

    def test_ColorRelief_512x512(self):
        color_context = self._color_context
        cartograher = GDALColorRelief(color_context=color_context,
                                      server=TEST_SVR,
                                      dem_table='world',
                                      image_type='gtiff')

        test_result = './output/test_cartographer_colorrelief_512x512.tif'
        if os.path.exists(test_result):
            os.remove(test_result)

        size = (512, 512)
        envelope = TEST_ENVELOPE
        data = cartograher.doodle(envelope, size)
        self.assert_(data)

        with open(test_result, 'wb') as fp:
            fp.write(data)

        cartograher.close()

    def test_ColorRelief_PNG(self):
        color_context = self._color_context
        cartograher = GDALColorRelief(color_context=color_context,
                                      server=TEST_SVR,
                                      dem_table='world',
                                      image_type='png')

        test_result = './output/test_cartographer_colorrelief_png.png'
        if os.path.exists(test_result):
            os.remove(test_result)

        size = (256, 256)
        envelope = TEST_ENVELOPE
        data = cartograher.doodle(envelope, size)
        self.assert_(data)

        with open(test_result, 'wb') as fp:
            fp.write(data)

        cartograher.close()

    def test_ColorRelief_JPEG(self):
        color_context = self._color_context
        cartograher = GDALColorRelief(color_context=color_context,
                                      server=TEST_SVR,
                                      dem_table='world',
                                      image_type='jpeg',
                                      image_parameters={'quality': 95})

        test_result = './output/test_cartographer_colorrelief_jpeg_95.jpg'
        if os.path.exists(test_result):
            os.remove(test_result)

        size = (256, 256)
        envelope = TEST_ENVELOPE
        data = cartograher.doodle(envelope, size)
        self.assert_(data)

        with open(test_result, 'wb') as fp:
            fp.write(data)

        cartograher.close()


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
