'''
Created on Sep 10, 2012

@author: ray
'''
import unittest
from mason.core import Pyramid, Format, MetaTile
from mason.renderer import MetaTileProcessorFactory


class MetaTileProcessorTest(unittest.TestCase):

    def testProcess(self):
        pyramid = Pyramid(tile_size=512)
        metatile_index = pyramid.create_metatile_index(3, 2, 2, 2)

        # make a fake metatile
        with open('./input/hailey.tif', 'rb') as fp:
            data = fp.read()
        data_fmt = Format.GTIFF
        metatile = MetaTile.from_tile_index(metatile_index, data, data_fmt, 0)

        prototype = MetaTileProcessorFactory.GDAL_HILLSHADING
        parameters = dict(zfactor=1, scale=111120, azimuth=315, altitude=45)
        processor = MetaTileProcessorFactory(prototype, **parameters)

        metatile_processed = processor.process(metatile)
        self.assertIsNotNone(metatile_processed.data)
        self.assertNotEqual(metatile_processed.data, metatile.data)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testProcess']
    unittest.main()
