'''
Created on May 11, 2012

@author: ray
'''
import os
import unittest
from mason.core.pyramid import Pyramid
from mason.tilesource import create_tile_source


def save_to_file(tag, ext, data):
    file_name = './output/test_tile_source_%(tag)s.%(ext)s' % \
                {'tag': tag, 'ext': ext}
    if os.path.exists(file_name):
        os.remove(file_name)
    with open(file_name, 'wb') as fp:
        fp.write(data)


class TestTileSource(unittest.TestCase):

    def setUp(self):
        config = dict(prototype='mapnik',
                       tag='text',
                       theme_root='./input/',
                       theme_name='worldaltas',
                       data_type='png'
                       )

        self._tile_source = create_tile_source(**config)
        self._pyramid = Pyramid()

    def testGetTile(self):
        z, x, y = 1, 1, 1
        tile_index = self._pyramid.create_tile_index(z, x, y)
        tile = self._tile_source.get_tile(tile_index)

        self.assertEqual(tile.index.coord, (z, x, y))
        self.assertIn('mtime', tile.metadata)
        self.assertIn('mimetype', tile.metadata)
        self.assert_(tile.data)

        save_to_file('worldaltas', tile.metadata['ext'], tile.data)

    def testGetMetaTile(self):
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
