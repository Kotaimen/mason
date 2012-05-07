'''
Created on May 2, 2012

@author: ray
'''
import os
import unittest
from mason.cartographer.mapnikmaker import MapnikRaster


class TestMapnikMaker(unittest.TestCase):

    def setUp(self):
        """ Natural Earth is a public domain world-wide data set
        available from http://naturalearthdata.com.
        """

        self._maker = MapnikRaster(theme_root='./input/',
                                   theme_name='worldaltas',
                                   image_type='png')

        self._mapnik_result = './output/worldaltas.png'
        if os.path.exists(self._mapnik_result):
            os.remove(self._mapnik_result)

    def testMapnikRaster(self):
        size = (256, 256)
        envelope = (-180, -85, 180, 85)
        data = self._maker.make(envelope, size)
        self.assert_(data)

        with open(self._mapnik_result, 'wb') as fp:
            fp.write(data)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
