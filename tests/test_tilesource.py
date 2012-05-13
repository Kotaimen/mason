'''
Created on May 11, 2012

@author: ray
'''
import os
import unittest
from mason.tilelib.pyramid import Pyramid
from mason.tilesource import create_tile_source


class TestTileSource(unittest.TestCase):

    def setUp(self):
        prototype = 'cartographer'
        cartographer_config = dict(prototype='mapniker',
                                   theme_root='./input/',
                                   theme_name='worldaltas',
                                   image_type='png'
                                   )

        tilesource_config = dict(cartographer_config=cartographer_config)

        self._tile_source = create_tile_source(prototype,
                                               'test',
                                               **tilesource_config)
        self._pyramid = Pyramid()

    def _save_test_result(self, name, data):
        if os.path.exists(name):
            os.remove(name)
        with open(name, 'wb') as fp:
            fp.write(data)

    def testGetTile(self):
        z, x, y = 1, 1, 1
        tile_index = self._pyramid.create_tile_index(z, x, y)
        tile = self._tile_source.get_tile(tile_index)

        self.assertEqual(tile.index.coord, (z, x, y))
        self.assertIn('timestamp', tile.metadata)
        self.assert_(tile.data)

        test_result = './output/worldaltas_tile_source.png'
        self._save_test_result(test_result, tile.data)

    def testGetMetaTile(self):
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
