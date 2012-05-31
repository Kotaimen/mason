'''
Created on Jun 1, 2012

@author: ray
'''
import unittest
from mason.core.pyramid import Pyramid


class TestTile(unittest.TestCase):

    def testTileEnvelopeBuffer(self):

        for tile_size in [256, 512]:
            pyramid = Pyramid(tile_size=tile_size)
            tile_index = pyramid.create_tile_index(2, 1, 1)

            envelope = tile_index.buffer_envelope(tile_size)

            lt_tile = pyramid.create_tile_index(2, 0, 0)
            rb_tile = pyramid.create_tile_index(2, 2, 2)

            self.assertEqual(envelope.lefttop, lt_tile.envelope.lefttop)
            self.assertEqual(envelope.rightbottom, rb_tile.envelope.rightbottom)

    def testMetaTileEnvelopeBuffer(self):

        for tile_size in [256, 512]:
            pyramid = Pyramid(tile_size=tile_size)
            metatile_index = pyramid.create_metatile_index(3, 2, 2, 2)

            envelope = metatile_index.buffer_envelope(tile_size)

            lt_tile = pyramid.create_tile_index(3, 1, 1)
            rb_tile = pyramid.create_tile_index(3, 4, 4)

            self.assertEqual(envelope.lefttop, lt_tile.envelope.lefttop)
            self.assertEqual(envelope.rightbottom, rb_tile.envelope.rightbottom)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
