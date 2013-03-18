'''
Created on Mar 17, 2013

@author: ray
'''
import os
import unittest
import shutil
from mason.core import Pyramid, Metadata, Tile
from mason.tilestorage import create_tilestorage
from mason.renderer.node import *


def get_test_context(z, x, y, sride):
    pyramid = Pyramid(levels=list(range(0, z + 1)))
    metatile_index = pyramid.create_metatile_index(z, x, y, sride)
    context = MetaTileContext(metatile_index)
    return context


def write(filename, data):
    with open(filename, 'wb') as fp:
        fp.write(data)


def read(filename):
    with open(filename, 'rb') as fp:
        return fp.read()


def remove(filename):
    if os.path.exists(filename):
        os.remove(filename)


class HillShadingRenderNodeTest(unittest.TestCase):

    def setUp(self):
        self._context = get_test_context(15, 5926, 11962, 2)

        # create a test metatile
        with open('./input/hailey.tif', 'rb') as fp:
            data = fp.read()
        metatile_index = self._context.metatile_index
        metatile = MetaTile.from_tile_index(metatile_index, data)

        # put metatile into the source pool
        key = 'elev' + repr(metatile_index)
        self._context.source_pool.put(key, metatile)

    def tearDown(self):
        pass

    def testRender(self):
        render_node = HillShadingRenderNode('dummy', source_names=['elev'],
                                            zfactor=1,
                                            scale=111120,
                                            altitude=45,
                                            azimuth=315)
        metatile = render_node.render(self._context)
        self.assertIsNotNone(metatile.data)
        remove('./output/hailey_hillshading1.tif')
        write('./output/hailey_hillshading1.tif', metatile.data)

    def testLambda(self):
        render_node = HillShadingRenderNode('dummy', source_names=['elev'],
                                            zfactor=lambda z, x, y: 10,
                                            scale=lambda z, x, y: 111120,
                                            altitude=lambda z, x, y: 45,
                                            azimuth=lambda z, x, y: 315)
        metatile = render_node.render(self._context)
        self.assertIsNotNone(metatile.data)
        remove('./output/hailey_hillshading2.tif')
        write('./output/hailey_hillshading2.tif', metatile.data)


class ColorReliefRenderNodeTest(unittest.TestCase):

    def setUp(self):
        self._context = get_test_context(15, 5926, 11962, 2)

        # create a test metatile
        with open('./input/hailey.tif', 'rb') as fp:
            data = fp.read()
        metatile_index = self._context.metatile_index
        metatile = MetaTile.from_tile_index(metatile_index, data)

        # put metatile into the source pool
        key = 'elev' + repr(metatile_index)
        self._context.source_pool.put(key, metatile)

        self._color_context = './input/hypsometric-map-world.txt'

    def tearDown(self):
        pass

    def testRender(self):
        render_node = ColorReliefRenderNode('dummy',
                                            ['elev'],
                                            self._color_context)
        metatile = render_node.render(self._context)
        self.assertIsNotNone(metatile.data)
        remove('./output/hailey_colorrelief.tif')
        write('./output/hailey_colorrelief.tif', metatile.data)


class StorageRenderNodeTest(unittest.TestCase):

    def setUp(self):
        pyramid = Pyramid(levels=range(21), format=Format.DATA)
        metadata = Metadata.make_metadata(
                            tag='StorageRender',
                            version='1.0.0')
        self._output_dir = os.path.join('output',
                                       'StorageRender')

        if os.path.exists(self._output_dir):
            shutil.rmtree(self._output_dir, ignore_errors=True)

        self._storage = create_tilestorage('filesystem',
                               pyramid,
                               metadata,
                               root=self._output_dir,
                               compress=False,
                               simple=False,)

        self._context = get_test_context(15, 5928, 11962, 2)
        metatile_index = self._context.metatile_index
        metatile = MetaTile.from_tile_index(metatile_index, b'test')
        self._storage.put(metatile)

    def tearDown(self):
        self._storage.close()

    def testRender(self):
        storage_cfg = dict(prototype='filesystem', root=self._output_dir)
        render_node = StorageRenderNode('storage', storage_cfg)
        metatile = render_node.render(self._context)
        self.assertEqual(metatile.data, b'test')


class MapnikRenderNodeTest(unittest.TestCase):

    def setUp(self):
        self._context = get_test_context(3, 2, 2, 2)

    def tearDown(self):
        pass

    def testRender(self):
        mapnik_cfg = dict(theme='./input/world.xml', image_type='png')
        render_node = MapnikRenderNode('mapnik', mapnik_cfg)
        metatile = render_node.render(self._context)
        self.assertIsNotNone(metatile.data)
        remove('./output/test_world.png')
        write('./output/test_world.png', metatile.data)


class RasterRenderNodeTest(unittest.TestCase):

    def setUp(self):
        self._context = get_test_context(15, 5928, 11962, 2)

    def tearDown(self):
        pass

    def testRender(self):
        dataset_cfg = dict(dataset_path='./input/hailey.tif')
        render_node = RasterRenderNode('raster', dataset_cfg)
        metatile = render_node.render(self._context)
        self.assertIsNotNone(metatile.data)
        remove('./output/test_dataset.tif')
        write('./output/test_dataset.tif', metatile.data)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
