'''
Created on May 2, 2012

@author: ray
'''

import os
import unittest
from mason.cartographer.gdaldemmaker import (GDALDEMRaster,
                                             GDALHillShade,
                                             GDALColorRelief,
                                             )


TEST_SVR = 'postgresql+psycopg2://postgres:123456@localhost:5432/world_dem'
TEST_TBL = 'world'
TEST_ENVELOPE = (103.9995833, 27.9995833, 104.5004167, 28.5004167)


class GDALRasterTest(unittest.TestCase):

    def setUp(self):
        self._maker = GDALDEMRaster(server=TEST_SVR,
                                    dem_table='world',
                                    image_type='gtiff')

        self._result = './output/test_result_raw'
        if os.path.exists(self._result):
            os.remove(self._result)

    def testGetDemData(self):
        envelope = TEST_ENVELOPE
        data = self._maker.get_dem_data(envelope)
        self.assert_(data)

        result = './output/test_result_raw'
        with open(result, 'wb') as fp:
            fp.write(data)


class GDALHillShadeTest(unittest.TestCase):

    def setUp(self):
        self._maker = GDALHillShade(server=TEST_SVR,
                                    dem_table='world',
                                    image_type='gtiff')

        self._result1 = './output/test_result_hillshade_256_256'
        if os.path.exists(self._result1):
            os.remove(self._result1)

        self._result2 = './output/test_result_hillshade_512_512'
        if os.path.exists(self._result2):
            os.remove(self._result2)

    def testMakeHillShade(self):
        size = (256, 256)
        envelope = TEST_ENVELOPE
        data = self._maker.make(envelope, size)
        self.assert_(data)

        with open(self._result1, 'wb') as fp:
            fp.write(data)

        size = (512, 512)
        envelope = TEST_ENVELOPE
        data = self._maker.make(envelope, size)
        self.assert_(data)

        with open(self._result2, 'wb') as fp:
            fp.write(data)


class GDALColorReliefTest(unittest.TestCase):

    def setUp(self):
        color_context = './input/HypsometricColors(Light).txt'
        self._maker = GDALColorRelief(color_context=color_context,
                                      server=TEST_SVR,
                                      dem_table='world',
                                      image_type='gtiff')

        self._result1 = './output/test_result_color_relief_256_256'
        if os.path.exists(self._result1):
            os.remove(self._result1)

        self._result2 = './output/test_result_color_relief_512_512'
        if os.path.exists(self._result2):
            os.remove(self._result2)

    def testMakeColorRelief(self):
        size = (256, 256)
        envelope = TEST_ENVELOPE
        data = self._maker.make(envelope, size)
        self.assert_(data)

        with open(self._result1, 'wb') as fp:
            fp.write(data)

        size = (512, 512)
        envelope = TEST_ENVELOPE
        data = self._maker.make(envelope, size)
        self.assert_(data)

        with open(self._result2, 'wb') as fp:
            fp.write(data)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
