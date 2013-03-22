# -*- coding:utf-8 -*-
'''
Created on Sep 13, 2012

@author: ray
'''
import unittest
from mason.config import MasonConfig, MasonRenderer


class TestMasonConfig(unittest.TestCase):

    def testGetNodeConfig(self):
        config = MasonConfig('./input/test_config.cfg.py')
        config.get_node_cfg('ROOT')


class TestMasonRenderer(unittest.TestCase):

    def setUp(self):
        config = MasonConfig('./input/test_config.cfg.py')
        self.renderer = MasonRenderer(config, 'overwrite')

    def tearDown(self):
        self.renderer.close()

    def testGetPyramid(self):
        pyramid = self.renderer.pyramid
        self.assertEqual(pyramid.envelope.make_tuple(), (-180, -85, 180, 85))

    def testGetMetadata(self):
        metadata = self.renderer.metadata
        self.assertEqual(metadata.tag, 'test-mason_renderer')

    def testRenderTile(self):
        pyramid = self.renderer.pyramid
        tile_index = pyramid.create_tile_index(3, 2, 2, False)
        tile = self.renderer.render_tile(tile_index)
        self.assertIsNotNone(tile.data)

        has_tile = self.renderer.has_tile(tile_index)
        self.assertTrue(has_tile)

    def testRenderMetaTile(self):
        pyramid = self.renderer.pyramid
        metatile_index = pyramid.create_metatile_index(3, 2, 2, 2)
        self.renderer.render_metatile(metatile_index)

        has_metatile = self.renderer.has_metatile(metatile_index)
        self.assertTrue(has_metatile)

    def testReadOnlyMode(self):
        config = MasonConfig('./input/test_config.cfg.py')
        renderer = MasonRenderer(config, 'readonly')

        pyramid = self.renderer.pyramid
        tile_index = pyramid.create_tile_index(5, 2, 2, False)

        # delete if exists
        renderer._storage.delete(tile_index)
        # assert the tile do not exists
        has_tile = renderer.has_tile(tile_index)
        self.assertFalse(has_tile)
        # readonly do not render tile
        tile = renderer.render_tile(tile_index)
        self.assertIsNone(tile)
        has_tile = renderer.has_tile(tile_index)
        self.assertFalse(has_tile)

        metatile_index = pyramid.create_metatile_index(5, 2, 2, 2)
        # delete if exists
        tile_indexes = metatile_index.fission()
        renderer._storage.delete_multi(tile_indexes)
        # assert the metatile do not exists
        has_metatile = self.renderer.has_metatile(metatile_index)
        self.assertFalse(has_metatile)
        # readonly do not render metatile
        renderer.render_metatile(metatile_index)
        has_metatile = self.renderer.has_metatile(metatile_index)
        self.assertFalse(has_metatile)

    def testHybridMode(self):
        config = MasonConfig('./input/test_config.cfg.py')
        renderer = MasonRenderer(config, 'hybrid')

        pyramid = renderer.pyramid
        tile_index = pyramid.create_tile_index(5, 2, 2, False)

        # delete if exists
        renderer._storage.delete(tile_index)
        # assert the tile do not exists
        has_tile = renderer.has_tile(tile_index)
        self.assertFalse(has_tile)
        # hybrid render a tile
        tile = renderer.render_tile(tile_index)
        self.assertIsNotNone(tile)
        has_tile = renderer.has_tile(tile_index)
        self.assertTrue(has_tile)

        metatile_index = pyramid.create_metatile_index(5, 2, 2, 2)
        # delete if exists
        tile_indexes = metatile_index.fission()
        renderer._storage.delete_multi(tile_indexes)
        # assert the metatile do not exists
        has_metatile = self.renderer.has_metatile(metatile_index)
        self.assertFalse(has_metatile)
        # hybrid render a metatile
        renderer.render_metatile(metatile_index)
        has_metatile = renderer.has_metatile(metatile_index)
        self.assertTrue(has_metatile)

    def testDryRunMode(self):
        config = MasonConfig('./input/test_config.cfg.py')
        renderer = MasonRenderer(config, 'dry-run')

        pyramid = renderer.pyramid
        tile_index = pyramid.create_tile_index(5, 2, 2, False)

        # delete if exists
        renderer._storage.delete(tile_index)
        # assert the tile do not exists
        has_tile = renderer.has_tile(tile_index)
        self.assertFalse(has_tile)
        # dry-run render a tile but do not store it
        tile = renderer.render_tile(tile_index)
        self.assertIsNotNone(tile)
        has_tile = renderer.has_tile(tile_index)
        self.assertFalse(has_tile)

        metatile_index = pyramid.create_metatile_index(5, 2, 2, 2)
        # delete if exists
        tile_indexes = metatile_index.fission()
        renderer._storage.delete_multi(tile_indexes)
        # assert the metatile do not exists
        has_metatile = self.renderer.has_metatile(metatile_index)
        self.assertFalse(has_metatile)
        # dry-run render a metatile but do not store it
        renderer.render_metatile(metatile_index)
        has_metatile = renderer.has_metatile(metatile_index)
        self.assertFalse(has_metatile)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
