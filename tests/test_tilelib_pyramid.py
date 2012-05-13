'''
Created on May 1, 2012

@author: Kotaimen
'''

import hashlib

import unittest
from mason.tilelib.pyramid import *


class Test(unittest.TestCase):

    def testPyramid(self):
        pyramid = Pyramid()
        self.assertEqual(pyramid.levels, range(0, 11))
        self.assertEqual(pyramid.tile_size, 256)
        self.assertEqual(pyramid.envelope.make_tuple(), (-180, -85.06, 180, 85.06))

    def testCreateTile(self):
        pyramid = Pyramid(levels=list(range(0, 10)),
                          envelope=(-180, -70, 0, 0))

        tile = pyramid.create_tile(2, 1, 2, b'data', {'metadata': None})

        self.assertEqual(tile.index.coord, (2, 1, 2))
        self.assertEqual(tile.index.z, 2)
        self.assertEqual(tile.index.x, 1)
        self.assertEqual(tile.index.y, 2)
        self.assertEqual(tile.index.serial, 14)
        self.assertEqual(tile.index.pixel_size, 256)

        self.assertAlmostEqual(tile.index.envelope.make_tuple(),
                          (-90.0, -66.51326044311185, 0.0, 0.0))

        self.assertEqual(tile.data, b'data')
        self.assertEqual(tile.datahash, hashlib.sha256(b'data').hexdigest())

    def testCreateMetaTileIndex(self):
        pyramid = Pyramid()

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


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
