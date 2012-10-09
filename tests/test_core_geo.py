'''
Created on May 1, 2012

@author: Kotaimen
'''

import unittest
from mason.core.geo import *


class TestCoordinate(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testInitDefault(self):
        coord = Coordinate()
        self.assertEqual(coord.longitude, 0)
        self.assertEqual(coord.latitude, 0)
        self.assertEqual(coord.lon, 0)
        self.assertEqual(coord.lat, 0)
        self.assertEqual(coord.crs, 'EPSG:4326')

    def testInit(self):
        coord = Coordinate(1.0, 2.0, 'EPSG:4326')
        self.assertEqual(coord.longitude, 1.0)
        self.assertEqual(coord.latitude, 2.0)
        self.assertEqual(coord.lon, 1.0)
        self.assertEqual(coord.lat, 2.0)
        self.assertEqual(coord.crs, 'EPSG:4326')

    def testMakeTuple(self):
        coord = Coordinate(1, 2)
        self.assertEqual(coord.longitude, 1)
        self.assertEqual(coord.latitude, 2)
        self.assertEqual(coord.make_tuple(), (1, 2))

    def testFromTuple(self):
        coord = Coordinate.from_tuple((1, 2))
        self.assertEqual(coord, Coordinate(1, 2))

    def testRepr(self):
        coord = Coordinate(1, 2)
        self.assertEqual(repr(coord), 'Coordinate(1, 2)')


class TestEnvelope(unittest.TestCase):

    def testInit(self):
        envelope = Envelope(0, 1, 2, 3)
        self.assertEqual(envelope.left, 0)
        self.assertEqual(envelope.bottom, 1)
        self.assertEqual(envelope.right, 2)
        self.assertEqual(envelope.top, 3)
        self.assertEqual(envelope.lefttop, Coordinate(0, 3))
        self.assertEqual(envelope.righttop, Coordinate(2, 3))
        self.assertEqual(envelope.leftbottom, Coordinate(0, 1))
        self.assertEqual(envelope.rightbottom, Coordinate(2, 1))
        self.assertEqual(envelope.crs, 'EPSG:4326')

    def testContains(self):
        envelope = Envelope(0, 1, 2, 3)
        self.assertTrue(envelope.contains(Coordinate(0.5, 1.5)))
        self.assertTrue(envelope.contains(Coordinate(0, 1)))
        self.assertTrue(envelope.contains(Coordinate(2, 3)))
        self.assertFalse(envelope.contains(Coordinate(3, 3)))

    def testIntersects(self):
        envelope = Envelope(0, 1, 2, 3)
        self.assertTrue(envelope.intersects(Envelope(0, 1, 2, 3)))
        self.assertTrue(envelope.intersects(Envelope(2, 3, 4, 5)))
        self.assertFalse(envelope.intersects(Envelope(4, 5, 6, 7)))
        self.assertTrue(envelope.intersects(Envelope(0.5, 1.5, 3, 4)))

    def testFromTuple(self):
        envelope = Envelope.from_tuple((0, 1, 2, 3))
        self.assertEqual(envelope, Envelope(0, 1, 2, 3))


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
