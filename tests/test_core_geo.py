'''
Created on May 1, 2012

@author: Kotaimen
'''

import unittest
from mason.core.geo import *


class TestSRID(unittest.TestCase):

    def testInit(self):
        srid = SRID('epsg', 4326)
        self.assertEqual(srid.authority, 'EPSG')
        self.assertEqual(srid.code, 4326)

    def testFromString(self):
        srid = SRID.from_string('epsg:4326')
        self.assertEqual(srid.authority, 'EPSG')
        self.assertEqual(srid.code, 4326)

    def testMakeTuple(self):
        srid = SRID('epsg', 4326)
        self.assertEqual(srid.make_tuple(), ('EPSG', 4326))


class TestDatum(unittest.TestCase):

    def testInit(self):
        srid = SRID.from_string('epsg:4326')
        wgs84 = Datum(srid)

        self.assertEqual(wgs84.srid.make_tuple(), srid.make_tuple())
        self.assertAlmostEqual(wgs84.semi_major, 6378137.0)
        self.assertAlmostEqual(wgs84.semi_minor, 6356752.3142, 4)
        self.assertAlmostEqual(1 / wgs84.flattening, 298.257223563, 9)


class TestSpatialTransformer(unittest.TestCase):

    def testTransform(self):
        source_srid = SRID.from_string('epsg:4326')
        target_srid = SRID.from_string('epsg:3857')

        transformer = SpatialTransformer(source_srid, target_srid)
        (x, y, z) = transformer.forward(-180.0, -85.0511287798065, 0.0)
        self.assertAlmostEqual(x, -20037508.3427892, 6)
        self.assertAlmostEqual(y, -20037508.3427892, 6)
        self.assertAlmostEqual(z, 0)

        (x, y, z) = transformer.forward(180.0, 85.0511287798065, 0.0)
        self.assertAlmostEqual(x, 20037508.3427892, 6)
        self.assertAlmostEqual(y, 20037508.3427892, 6)
        self.assertAlmostEqual(z, 0)

        (x, y, z) = transformer.forward(0.0, 0.0, 0.0)
        self.assertAlmostEqual(x, 0)
        self.assertAlmostEqual(y, 0)
        self.assertAlmostEqual(z, 0)

        (x, y, z) = transformer.reverse(20037508.3427892, 20037508.3427892, 0.0)
        self.assertAlmostEqual(x, 180.0)
        self.assertAlmostEqual(y, 85.0511287798065)
        self.assertAlmostEqual(z, 0.0)

        (x, y, z) = transformer.reverse(-20037508.3427892, -20037508.3427892, 0.0)
        self.assertAlmostEqual(x, -180.0)
        self.assertAlmostEqual(y, -85.0511287798065)
        self.assertAlmostEqual(z, 0.0)

    def testNullTransform(self):
        source_srid = SRID.from_string('epsg:4326')
        target_srid = SRID.from_string('epsg:4326')

        transformer = SpatialTransformer(source_srid, target_srid)
        (x, y, z) = transformer.forward(180.0, 0.0, 0.0)
        self.assertEqual(x, 180.0)
        self.assertEqual(y, 0)
        self.assertEqual(z, 0)


class TestCoordinate(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testInitDefault(self):
        coord = Location()
        self.assertEqual(coord.x, 0)
        self.assertEqual(coord.y, 0)
        self.assertEqual(coord.z, 0)
        self.assertEqual(coord.srid, SRID('EPSG', 4326))

    def testInit(self):
        coord = Location(1.0, 2.0, 3.0, SRID('EPSG', 3857))
        self.assertEqual(coord.x, 1.0)
        self.assertEqual(coord.y, 2.0)
        self.assertEqual(coord.z, 3.0)
        self.assertEqual(coord.srid, SRID('EPSG', 3857))

    def testMakeTuple(self):
        coord = Location(1, 2, 3)
        self.assertEqual(coord.x, 1)
        self.assertEqual(coord.y, 2)
        self.assertEqual(coord.z, 3)
        self.assertEqual(coord.make_tuple(), (1, 2, 3))

    def testFromTuple(self):
        coord = Location.from_tuple((1, 2, 3))
        self.assertEqual(coord, Location(1, 2, 3))

    def testRepr(self):
        coord = Location(1, 2, 3)
        self.assertEqual(repr(coord), "Location(1, 2, 3, SRID('EPSG', 4326))")


class TestEnvelope(unittest.TestCase):

    def testInit(self):
        test_srid = SRID('EPSG', 3857)
        envelope = Envelope(0, 1, 2, 3, test_srid)
        self.assertEqual(envelope.left, 0)
        self.assertEqual(envelope.bottom, 1)
        self.assertEqual(envelope.right, 2)
        self.assertEqual(envelope.top, 3)
        self.assertEqual(envelope.lefttop, Location(0, 3, srid=test_srid))
        self.assertEqual(envelope.righttop, Location(2, 3, srid=test_srid))
        self.assertEqual(envelope.leftbottom, Location(0, 1, srid=test_srid))
        self.assertEqual(envelope.rightbottom, Location(2, 1, srid=test_srid))
        self.assertEqual(envelope.srid, SRID('EPSG', 3857))

    def testIntersects(self):
        test_srid = SRID('EPSG', 3857)
        envelope = Envelope(0, 1, 2, 3, test_srid)
        self.assertTrue(envelope.intersects(Envelope(0, 1, 2, 3, test_srid)))
        self.assertTrue(envelope.intersects(Envelope(2, 3, 4, 5, test_srid)))
        self.assertFalse(envelope.intersects(Envelope(4, 5, 6, 7, test_srid)))
        self.assertTrue(envelope.intersects(Envelope(0.5, 1.5, 3, 4, test_srid)))

    def testFromTuple(self):
        envelope = Envelope.from_tuple((0, 1, 2, 3))
        self.assertEqual(envelope, Envelope(0, 1, 2, 3))


class TestProjection(unittest.TestCase):

    def setUp(self):
        self.proj = GoogleMercatorProjection()

    def testProject(self):
        coord = Location(0, 0)
        self.assertEqual(self.proj.project(coord), Point(0.5, 0.5))

    def testUnproject(self):
        point = Point(0.5, 0.5)
        self.assertEqual(self.proj.unproject(point), Location(0, 0))

    def testTileEnvelope(self):
        z, x, y = 0, 0, 0
        self.assertEqual(self.proj.tile_envelope(z, x, y).make_tuple(),
                        (-180, -85.051128779806589, 180, 85.051128779806604))


class TestTileCoordinates(unittest.TestCase):

    def testCoord2Serial(self):

        self.assertEqual(tile_coordinate_to_serial(0, 0, 0), 0)
        self.assertEqual(tile_coordinate_to_serial(8, 8, 8), 23901)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
