'''
Created on May 19, 2012

@author: ray
'''
import unittest
from mason.composer.imagemagick import ImageMagickComposer
from mason.tilelib.pyramid import Pyramid


class TestImageMagicComposer(unittest.TestCase):

    def setUp(self):
        command = 'convert $1 $2 -compose lighten -composite png:-'
        self._composer = ImageMagickComposer('test', command)
        self._pyramid = Pyramid()

    def tearDown(self):
        pass

    def testCompose(self):
        test_images = ['./input/test_compose1.tif',
                       './input/test_compose2.tif',
                       ]
        test_result = './output/compose_result.png'

        tiles = list()
        for image in test_images:
            with open(image, 'rb') as fp:
                data = fp.read()

            metadata = dict()
            metadata['ext'] = 'tif'

            tile = self._pyramid.create_tile(0, 0, 0, data, metadata)
            tiles.append(tile)

        data = self._composer.compose(tiles)
        with open(test_result, 'wb') as fp:
            fp.write(data)

        self.assert_(data)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
