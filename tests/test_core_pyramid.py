'''
Created on May 1, 2012

@author: Kotaimen
'''

import hashlib
import os, os.path

import unittest

from mason.core.pyramid import Pyramid
from mason.core.tile import Tile, MetaTile
from mason.core.format import Format


class TestPyramid(unittest.TestCase):

    def testDefaultParameters(self):

        pyramid = Pyramid()
        self.assertEqual(pyramid.levels, range(0, 11))
        self.assertEqual(pyramid.tile_size, 256)
        self.assertEqual(pyramid.buffer, 0)
        self.assertEqual(pyramid.format.name, 'ANY')
        self.assertEqual(pyramid.center.make_tuple(), (121.3, 31.1))
        self.assertEqual(pyramid.zoom, 0)
        self.assertEqual(pyramid.envelope.make_tuple(), (-180, -85.06, 180, 85.06))

    def testSummarize(self):
        pyramid = Pyramid(buffer=16, format=Format.PNG)
        import json
        jsonstr = json.dumps(pyramid.summarize(), indent=4)
        pythonobj = json.loads(jsonstr)
        pyramid2 = Pyramid.from_summary(pythonobj)
        self.assertEqual(pyramid.format, pyramid2.format)

    def testCreateTile(self):
        pyramid = Pyramid(levels=list(range(0, 10)),
                          envelope=(-180, -70, 0, 0))

        index = pyramid.create_tile_index(2, 1, 2)
        tile = Tile.from_tile_index(index, b'data')

        self.assertEqual(tile.index.coord, (2, 1, 2))
        self.assertEqual(tile.index.z, 2)
        self.assertEqual(tile.index.x, 1)
        self.assertEqual(tile.index.y, 2)
        self.assertEqual(tile.index.serial, 14)
        self.assertEqual(tile.index.tile_size, 256)

        self.assertEqual(tile.index.envelope.make_tuple(),
                         (-90.0, -66.51326044311185, 0.0, 0.0))

        self.assertEqual(tile.index.buffered_envelope.make_tuple(),
                         (-90.0, -66.51326044311185, 0.0, 0.0))

        self.assertEqual(tile.data, b'data')
        self.assertEqual(tile.data_hash, hashlib.sha256(b'data').hexdigest())

    def testCreateTileBuffered(self):
        pyramid = Pyramid(levels=list(range(0, 10)),
                          envelope=(0, 0, 90, 50),
                          buffer=32,
                          tile_size=512)

        index = pyramid.create_tile_index(2, 2, 1)
        tile = Tile.from_tile_index(index, b'data2')

        self.assertEqual(tile.index.coord, (2, 2, 1))
        self.assertEqual(tile.index.z, 2)
        self.assertEqual(tile.index.x, 2)
        self.assertEqual(tile.index.y, 1)
        self.assertEqual(tile.index.serial, 11)
        self.assertEqual(tile.index.tile_size, 512)
        self.assertEqual(tile.index.buffered_tile_size, 576)

        self.assertEqual(tile.index.buffered_envelope.make_tuple(),
                         (-5.625, -5.615985819155327, 95.625, 68.65655498475735))

        self.assertEqual(tile.data, b'data2')
        self.assertEqual(tile.data_hash, hashlib.sha256(b'data2').hexdigest())

    def testCreateMetaTileIndex(self):
        pyramid = Pyramid(buffer=32)

        index = pyramid.create_metatile_index(1, 0, 0, 16)
        self.assertEqual(index.coord, (1, 0, 0))
        self.assertEqual(index.stride, 2)

        index = pyramid.create_metatile_index(10, 0, 0, 16)
        self.assertEqual(index.coord, (10, 0, 0))
        self.assertEqual(index.stride, 16)

        index = pyramid.create_metatile_index(10, 13, 7, 16)
        self.assertEqual(index.coord, (10, 0, 0))
        self.assertEqual(index.stride, 16)

        index = pyramid.create_metatile_index(10, 49, 21, 16)
        self.assertEqual(index.coord, (10, 48, 16))
        self.assertEqual(index.stride, 16)

    def testCreateMetaTile(self):
        pyramid = Pyramid()

        index = pyramid.create_metatile_index(4, 1, 2, 2)
        tile = MetaTile.from_tile_index(index, b'data')

    def testClone(self):
        pyramid1 = Pyramid()
        pyramid2 = pyramid1.clone(format=Format.JPG)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
