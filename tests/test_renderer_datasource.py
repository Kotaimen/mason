'''
Created on Sep 10, 2012

@author: ray
'''
import unittest
from mason.core import Pyramid
from mason.renderer import MetaTileDataSourceFactory


class MetaTileDataSourceTest(unittest.TestCase):

    def testGet(self):
        pyramid = Pyramid(tile_size=512)
        metatile_index = pyramid.create_metatile_index(3, 2, 2, 2)

        prototype = MetaTileDataSourceFactory.CARTO_MAPNIK
        parameters = dict(theme='./input/world.xml', image_type='png')
        datasource = MetaTileDataSourceFactory(prototype, **parameters)
        metatile = datasource.get(metatile_index)

        self.assertIsNotNone(metatile)
        self.assertIsNotNone(metatile.data)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
