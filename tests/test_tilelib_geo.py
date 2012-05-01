'''
Created on May 1, 2012

@author: Kotaimen
'''

import unittest
from mason.tilelib.geo import *


class TestCoordinate(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testInit(self):
        coord = Coordinate()
        self.assertEqual(coord.longitude, 0)
        self.assertEqual(coord.latitude, 0)
        self.assertEqual(coord.lon, 0)
        self.assertEqual(coord.lat, 0)
        self.assertEqual(coord.crs, 4326)

    def testMakeTuple(self):
        coord = Coordinate(1, 2)
        self.assertEqual(coord.longitude, 1)
        self.assertEqual(coord.latitude, 2)
        self.assertEqual(coord.make_tuple(), (1, 2))


class TestProjection(unittest.TestCase):

    def setUp(self):
        self.proj = GoogleMercatorProjection()

    def testProject(self):
        coord = Coordinate(0, 0)
        self.assertEqual(self.proj.project(coord), Point(0.5, 0.5))

    def testUnproject(self):
        point = Point(0.5, 0.5)
        self.assertEqual(self.proj.unproject(point), Coordinate(0, 0))

    def testTileEnvelope(self):
        z, x, y = 0, 0, 0
        self.assertEqual(self.proj.tile_envelope(z, x, y).make_tuple(),
                        (-180, -85.051128779806589, 180, 85.051128779806604))


class TestTileCoordinates(unittest.TestCase):

    def testCoord2Serial(self):

        self.assertEqual(tile_coordinate_to_serial(0, 0, 0), 0)
        self.assertEqual(tile_coordinate_to_serial(8, 8, 8), 23901)



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
