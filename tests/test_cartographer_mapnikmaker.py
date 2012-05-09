'''
Created on May 2, 2012

@author: ray
'''
import os
import unittest
from mason.cartographer.mapnikmaker import MapnikRaster


class TestMapnikMaker(unittest.TestCase):

    def setUp(self):
        pass

    def testTrueColor(self):
        maker = MapnikRaster(theme_root='./input/',
                             theme_name='worldaltas',
                             image_type='png')

        size = (256, 256)
        envelope = (-180, -85, 180, 85)
        data = maker.make(envelope, size)
        self.assert_(data)

        test_result = './output/worldaltas.png'
        if os.path.exists(test_result):
            os.remove(test_result)

        with open(test_result, 'wb') as fp:
            fp.write(data)

    def testIndexColor(self):
        maker = MapnikRaster(theme_root='./input/',
                             theme_name='worldaltas',
                             image_type='png256',
                             image_parameters={'colors': 5}
                            )

        size = (256, 256)
        envelope = (-180, -85, 180, 85)
        data = maker.make(envelope, size)
        self.assert_(data)

        test_result = './output/worldaltas_index_color.png'
        if os.path.exists(test_result):
            os.remove(test_result)

        with open(test_result, 'wb') as fp:
            fp.write(data)

    def testTransparency(self):
        maker = MapnikRaster(theme_root='./input/',
                             theme_name='worldaltas',
                             image_type='png256',
                             image_parameters={'transparency': 1}
                            )

        size = (256, 256)
        envelope = (-180, -85, 180, 85)
        data = maker.make(envelope, size)
        self.assert_(data)

        test_result = './output/worldaltas_index_color_transparency.png'
        if os.path.exists(test_result):
            os.remove(test_result)

        with open(test_result, 'wb') as fp:
            fp.write(data)

    def testPalette(self):
        maker = MapnikRaster(theme_root='./input/',
                             theme_name='worldaltas',
                             image_type='png256',
                             image_parameters={
                                'palette': './input/example-palette.act'
                             }
                            )

        size = (256, 256)
        envelope = (-180, -85, 180, 85)
        data = maker.make(envelope, size)
        self.assert_(data)

        test_result = './output/worldaltas_index_color_palette.png'
        if os.path.exists(test_result):
            os.remove(test_result)

        with open(test_result, 'wb') as fp:
            fp.write(data)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
