'''
Created on May 2, 2012

@author: ray
'''
import os
import unittest
from mason.cartographer.mapniker import MapnikRaster


class TestMapnikMaker(unittest.TestCase):

    def setUp(self):
        pass

    def _save_test_result(self, name, data):
        if os.path.exists(name):
            os.remove(name)
        with open(name, 'wb') as fp:
            fp.write(data)

    def testTrueColor(self):
        maker = MapnikRaster(theme_root='./input/',
                             theme_name='worldaltas',
                             image_type='png')

        size = (256, 256)
        envelope = (-180, -85, 180, 85)
        data = maker.doodle(envelope, size)
        self.assert_(data)

        test_result = './output/worldaltas.png'
        self._save_test_result(test_result, data)

        maker.close()

    def testIndexColor(self):
        maker = MapnikRaster(theme_root='./input/',
                             theme_name='worldaltas',
                             image_type='png256',
                             image_parameters={'colors': 5}
                            )

        size = (256, 256)
        envelope = (-180, -85, 180, 85)
        data = maker.doodle(envelope, size)
        self.assert_(data)

        test_result = './output/worldaltas_index_color.png'
        self._save_test_result(test_result, data)

        maker.close()

    def testTransparency(self):
        maker = MapnikRaster(theme_root='./input/',
                             theme_name='worldaltas',
                             image_type='png256',
                             image_parameters={'transparency': 0}
                            )

        size = (256, 256)
        envelope = (-180, -85, 180, 85)
        data = maker.doodle(envelope, size)
        self.assert_(data)

        test_result = './output/worldaltas_index_color_transparency.png'
        self._save_test_result(test_result, data)

        maker.close()

    def testPalette(self):
        maker = MapnikRaster(theme_root='./input/',
                             theme_name='worldaltas',
                             image_type='png256',
                             image_parameters={
                                'palette': './input/example-palette.act',
                                'colors': 5,
                             }
                            )

        size = (256, 256)
        envelope = (-180, -85, 180, 85)
        data = maker.doodle(envelope, size)
        self.assert_(data)

        test_result = './output/worldaltas_index_color_palette.png'
        self._save_test_result(test_result, data)

        maker.close()

    def testJPEG(self):
        jpeg_quality = 50
        maker = MapnikRaster(theme_root='./input/',
                             theme_name='worldaltas',
                             image_type='jpeg',
                             image_parameters={
                                'quality': jpeg_quality,
                             }
                            )

        size = (256, 256)
        envelope = (-180, -85, 180, 85)
        data = maker.doodle(envelope, size)
        self.assert_(data)

        test_result = './output/worldaltas_JPEG_%d.jpeg' % jpeg_quality
        self._save_test_result(test_result, data)

        maker.close()

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
