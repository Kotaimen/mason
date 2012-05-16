'''
Created on May 1, 2012

@author: Kotaimen
'''

import hashlib
import os, os.path

import unittest
from mason.tilelib.pyramid import *


class TestPyramid(unittest.TestCase):

    def setUp(self):
        if not os.path.exists(r'./output/grid'):
            os.mkdir(r'./output/grid')

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

    def testCreateDummyMetaTile(self):
        pyramid = Pyramid()

        tile1 = pyramid.create_tile(2, 0, 0, b'data1', {})
        tile2 = pyramid.create_tile(2, 0, 1, b'data2', {})
        tile3 = pyramid.create_tile(2, 1, 0, b'data3', {})
        tile4 = pyramid.create_tile(2, 1, 1, b'data4', {})

        metatile = pyramid.create_dummy_metatile(2, 0, 0, 2, [tile1, tile2, tile3, tile4])

        self.assertEqual(metatile.data, b'')
        self.assertEqual(metatile.fission(), [tile1, tile2, tile3, tile4])

    def testCreateMetaTilePNG(self):
        pyramid = Pyramid()
        with open(r'./input/grid.png', 'rb') as fp:
            data = fp.read()
        metadata = dict(ext='png', mimetype='image/png')
        metatile = pyramid.create_metatile(8, 0, 0, 4, data, metadata)
        for tile in metatile.fission():
            with open(os.path.join(r'./output/grid',
                                   '%d-%d-%d.png' % tile.index.coord), 'wb') as fp:
                fp.write(tile.data)

    def testCreateMetaTileJPEG(self):
        pyramid = Pyramid()
        with open(r'./input/grid.jpg', 'rb') as fp:
            data = fp.read()
        metadata = dict(ext='jpg', mimetype='image/jpeg')
        metatile = pyramid.create_metatile(8, 0, 0, 4, data, metadata)
        for tile in metatile.fission():
            with open(os.path.join(r'./output/grid',
                                   '%d-%d-%d.jpg' % tile.index.coord), 'wb') as fp:
                fp.write(tile.data)

    def testCreateMetaTileTIFF(self):
        pyramid = Pyramid()
        with open(r'./input/grid.tif', 'rb') as fp:
            data = fp.read()
        metadata = dict(ext='tif', mimetype='image/tiff')
        metatile = pyramid.create_metatile(8, 0, 0, 4, data, metadata)
        for tile in metatile.fission():
            with open(os.path.join(r'./output/grid',
                                   '%d-%d-%d.tif' % tile.index.coord), 'wb') as fp:
                fp.write(tile.data)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
