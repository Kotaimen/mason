'''
Created on May 1, 2012

@author: Kotaimen
'''
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

        tile = pyramid.create_tile(2, 1, 2, b'data', {'metadata':None})

        self.assertEqual(tile.index.coord, (2, 1, 2))
        self.assertAlmostEqual(tile.index.envelope.make_tuple(),
                          (-90.0, -66.51326044311185, 0.0, 0.0))
        self.assertEqual(tile.data, b'data')


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
