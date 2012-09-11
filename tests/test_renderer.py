'''
Created on Sep 10, 2012

@author: ray
'''
import os
import unittest
from mason.core import Pyramid, Format, Metadata, MetaTile
from mason.tilestorage import TileStorageFactory
from mason.renderer import (MetaTileDataSourceFactory,
                            MetaTileProcessorFactory,
                            MetaTileComposerFactory,
                            MetaTileRendererFactory,
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

        # data source
        prototype = MetaTileDataSourceFactory.CARTO_MAPNIK
        parameters = dict(theme='./input/world.xml', image_type='png')
        datasource = MetaTileDataSourceFactory(prototype, **parameters)

        # renderer
        prototype = MetaTileRendererFactory.DATASOURCE_RENDERER
        renderer = MetaTileRendererFactory(prototype, datasource=datasource)

        metatile = renderer.render(metatile_index)
        self.assertIsNotNone(metatile.data)
        self.assertEqual(metatile.format, Format.PNG)

    def testProcessingMetaTileRenderer(self):
        pyramid = Pyramid(tile_size=512)
        metatile_index = pyramid.create_metatile_index(3, 2, 2, 2)

        # processor
        prototype = MetaTileProcessorFactory.GDAL_HILLSHADING
        parameters = dict(zfactor=1, scale=111120, azimuth=315, altitude=45)
        processor = MetaTileProcessorFactory(prototype, **parameters)

        # renderer
        prototype = MetaTileRendererFactory.PROCESSING_RENDERER
        source_renderer = FakeRenderer()
        renderer = MetaTileRendererFactory(prototype,
                                           processor=processor,
                                           source_renderer=source_renderer)

        metatile = renderer.render(metatile_index)
        self.assertIsNotNone(metatile.data)
        self.assertEqual(metatile.format, Format.GTIFF)

    def testCompositeMetaTileRenderer(self):
        pyramid = Pyramid(tile_size=512)
        metatile_index = pyramid.create_metatile_index(3, 2, 2, 2)

        # composer
        prototype = MetaTileComposerFactory.IM
        parameters = dict(command='')
        composer = MetaTileComposerFactory(prototype, **parameters)

        # renderer
        prototype = MetaTileRendererFactory.COMPOSITE_RENDERER
        renderer1 = FakeRenderer()
        renderer2 = FakeRenderer()
        renderer3 = FakeRenderer()
        source_renderers = [renderer1, renderer2, renderer3]
        renderer = MetaTileRendererFactory(prototype,
                                           composer=composer,
                                           source_renderers=source_renderers)

        metatile = renderer.render(metatile_index)
        self.assertIsNotNone(metatile.data)
        self.assertEqual(metatile.format, Format.ANY)

    def testCachedRenderer(self):
        pyramid = Pyramid(tile_size=512, format=Format.PNG)
        metatile_index = pyramid.create_metatile_index(3, 2, 2, 2)

        # data source
        prototype = MetaTileDataSourceFactory.CARTO_MAPNIK
        parameters = dict(theme='./input/world.xml', image_type='png')
        datasource = MetaTileDataSourceFactory(prototype, **parameters)

        # renderer
        prototype = MetaTileRendererFactory.DATASOURCE_RENDERER
        renderer = MetaTileRendererFactory(prototype, datasource=datasource)

        # storage
        metadata = Metadata.make_metadata(tag='TestFileSystemTileStorage',
                                          version='1.0.0.0.0.0')
        output_dir = os.path.join('output', 'TestFileSystemTileStorageDefault')
        storage = TileStorageFactory()('filesystem',
                                       pyramid=pyramid,
                                       metadata=metadata,
                                       root=output_dir,
                                       compress=False,
                                       simple=False,)

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
