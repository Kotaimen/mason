'''
Created on May 19, 2012

@author: ray
'''
import unittest
from mason.composer import create_tile_composer
from mason.tilelib.pyramid import Pyramid


class TestImageMagicComposer(unittest.TestCase):

    def setUp(self):
        command = '$1 $2 -compose lighten -composite'
        self._composer = create_tile_composer('imagemagick', 'test',
                                              command=command)
        self._pyramid = Pyramid()

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

        renderdata = self._composer.compose(tiles)
        self.assert_(renderdata.data)
        with open(test_result, 'wb') as fp:
            fp.write(renderdata.data)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
