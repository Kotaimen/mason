'''
Created on Mar 22, 2013

@author: ray
'''
import unittest
from mason.core import Pyramid, Metadata
from mason.renderer import create_render_node
from mason.tilestorage import create_tilestorage


class TestRenderNodeFactory(unittest.TestCase):

    def testCreateHillShadingRenderNode(self):
        pyramid = Pyramid()
        metadata = Metadata.make_metadata('test-hillshading')
        cache = create_tilestorage('metacache',
                                   pyramid=pyramid,
                                   metadata=metadata,
                                   root='./output/test_render_node_factory/')
        render_node = create_render_node('node.hillshading',
                                         'test',
                                         cache=cache,
                                         zfactor=1,
                                         scale=111120,
                                         altitude=45,
                                         azimuth=315
                                         )
        self.assertEqual(repr(render_node), "HillShadingRenderNode('test')")

    def testCreateColorReliefRenderNode(self):
        pyramid = Pyramid()
        metadata = Metadata.make_metadata('test-colorrelief')
        cache = create_tilestorage('metacache',
                                   pyramid=pyramid,
                                   metadata=metadata,
                                   root='./output/test_render_node_factory/')
        render_node = create_render_node('node.colorrelief',
                                         'test',
                                         cache=cache,
                                         color_context=''
                                         )
        self.assertEqual(repr(render_node), "ColorReliefRenderNode('test')")

    def testCreateStorageRenderNode(self):
        pyramid = Pyramid()
        metadata = Metadata.make_metadata('test-storage')
        cache = create_tilestorage('metacache',
                                   pyramid=pyramid,
                                   metadata=metadata,
                                   root='./output/test_render_node_factory/')

        storage_cfg = dict(prototype='filesystem',
                           root='./output/test_render_node_factory/')
        render_node = create_render_node('node.storage',
                                         'test',
                                         cache=cache,
                                         storage_cfg=storage_cfg
                                         )
        self.assertEqual(repr(render_node), "StorageRenderNode('test')")

    def testCreateMapnikRenderNode(self):
        pyramid = Pyramid()
        metadata = Metadata.make_metadata('test-mapnik')
        cache = create_tilestorage('metacache',
                                   pyramid=pyramid,
                                   metadata=metadata,
                                   root='./output/test_render_node_factory/')

        mapnik_cfg = dict(theme='./input/world.xml', image_type='png')
        render_node = create_render_node('node.mapnik',
                                         'test',
                                         cache=cache,
                                         **mapnik_cfg
                                         )
        self.assertEqual(repr(render_node), "MapnikRenderNode('test')")

    def testCreateRasterRenderNode(self):
        pyramid = Pyramid()
        metadata = Metadata.make_metadata('test-raster')
        cache = create_tilestorage('metacache',
                                   pyramid=pyramid,
                                   metadata=metadata,
                                   root='./output/test_render_node_factory/')

        dataset_cfg = dict(dataset_path='./input/hailey.tif')
        render_node = create_render_node('node.raster',
                                         'test',
                                         cache=cache,
                                         **dataset_cfg
                                         )
        self.assertEqual(repr(render_node), "RasterRenderNode('test')")

    def testCreateImageMagicRenderNode(self):
        pyramid = Pyramid()
        metadata = Metadata.make_metadata('test-imagemagic')
        cache = create_tilestorage('metacache',
                                   pyramid=pyramid,
                                   metadata=metadata,
                                   root='./output/test_render_node_factory/')
        render_node = create_render_node('node.imagemagick',
                                         'test',
                                         format='PNG',
                                         command='',
                                         cache=cache,
                                         )
        self.assertEqual(repr(render_node), "ImageMagicRenderNode('test')")


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
