'''
Created on Sep 10, 2012

@author: ray
'''
import os
import unittest
from mason.core import Pyramid, Format, Metadata, MetaTile
from mason.tilestorage import TileStorageFactory
from mason.renderer import (DataSourceRendererFactory,
                            ProcessingRendererFactory,
                            CompositeRendererFactory,
                            CachedRenderer,
                            )
from mason.renderer.renderer import MetaTileRenderer


class FakeRenderer(MetaTileRenderer):

    def render(self, metatileindex):
        with open('./input/hailey.tif', 'rb') as fp:
            data = fp.read()
        data_fmt = Format.GTIFF
        metatile = MetaTile.from_tile_index(metatileindex, data, data_fmt, 0)
        return metatile


class RendererTest(unittest.TestCase):

    def testDataSourceMetaTileRenderer(self):
        pyramid = Pyramid(tile_size=512)
        metatile_index = pyramid.create_metatile_index(3, 2, 2, 2)

        params = dict(theme='./input/world.xml', image_type='png')
        renderer = DataSourceRendererFactory('mapnik', **params)

        metatile = renderer.render(metatile_index)
        self.assertIsNotNone(metatile.data)
        self.assertEqual(metatile.format, Format.PNG)

    def testProcessingMetaTileRenderer(self):
        pyramid = Pyramid(tile_size=512)
        metatile_index = pyramid.create_metatile_index(3, 2, 2, 2)

        # processor
        params = dict(zfactor=1, scale=111120, azimuth=315, altitude=45)
        source_renderer = FakeRenderer()
        renderer = ProcessingRendererFactory('hillshading', source_renderer, **params)

        metatile = renderer.render(metatile_index)
        self.assertIsNotNone(metatile.data)
        self.assertEqual(metatile.format, Format.GTIFF)

    def testCompositeMetaTileRenderer(self):
        pyramid = Pyramid(tile_size=512)
        metatile_index = pyramid.create_metatile_index(3, 2, 2, 2)

        # composer
        params = dict(command='')

        # renderer
        renderer1 = FakeRenderer()
        renderer2 = FakeRenderer()
        renderer3 = FakeRenderer()
        source_list = [renderer1, renderer2, renderer3]
        renderer = CompositeRendererFactory('imagemagick', source_list, **params)

        metatile = renderer.render(metatile_index)
        self.assertIsNotNone(metatile.data)
        self.assertEqual(metatile.format, Format.ANY)

    def testCachedRenderer(self):
        pyramid = Pyramid(tile_size=512, format=Format.PNG)
        metatile_index = pyramid.create_metatile_index(3, 2, 2, 2)

        params = dict(theme='./input/world.xml', image_type='png')
        renderer = DataSourceRendererFactory('mapnik', **params)

        # storage
        metadata = Metadata.make_metadata(tag='TestCachedRenderer')
        output_dir = os.path.join('output', 'TestCachedRenderer')
        storage = TileStorageFactory()('metacache',
                                        pyramid=pyramid,
                                        metadata=metadata,
                                        root=output_dir,
                                        compress=False,)

        # cached renderer
        cached_renderer = CachedRenderer(storage, renderer)

        metatile = cached_renderer.render(metatile_index)
        self.assertIsNotNone(metatile.data)
        self.assertEqual(metatile.format, Format.PNG)

        metatile_cached = storage.get(metatile_index)
        self.assertEqual(metatile.data, metatile_cached.data)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
