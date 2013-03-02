'''
Created on Sep 7, 2012

@author: Kotaimen
'''
import unittest

from mason.core.pyramid import Pyramid
from mason.core.geo import Location, SRID
from mason.core.walker import PyramidWalker


class TestWalker(unittest.TestCase):

    def testProj(self):
        srid = SRID.from_string('epsg:4326')
        pyramid = Pyramid()
        self.assertEqual(pyramid.coords_wgs842xyz(Location(-180, 85, srid=srid), 6), (0, 0))
        self.assertEqual(pyramid.coords_wgs842xyz(Location(-180, -85, srid=srid), 6), (0, 2 ** 6 - 1))
        self.assertEqual(pyramid.coords_wgs842xyz(Location(180, -85, srid=srid), 6), (2 ** 6 - 1, 2 ** 6 - 1))

    def testWalk(self):
        pyramid = Pyramid()
        walker = PyramidWalker(pyramid, [5], 4, (-180, -5, 180, 5))

        all_x = list()

        for index in walker.walk():
            all_x.append(index.x)
        self.assertEqual(min(all_x), 0)
        self.assertEqual(max(all_x), 28)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
