'''
Created on Mar 22, 2013

@author: ray
'''
import unittest
from mason.core import Pyramid, MetaTile, Format
from mason import renderer


def create_metatile_index(z, x, y, stride):
    pyramid = Pyramid()
    index = pyramid.create_metatile_index(z, x, y, stride=2)
    return index


class MockCache(object):

    def __init__(self):
        self._cache = dict()

    def put(self, metatile):
        self._cache[metatile.index] = metatile

    def get(self, metatile_index):
        return self._cache.get(metatile_index, None)


class MockChildNode(renderer.MetaTileRenderNode):

    def _render_impl(self, context, source_nodes):
        with open('./input/hailey.tif', 'rb') as fp:
            data = fp.read()
        metatile_index = context.metatile_index
        metatile = MetaTile.from_tile_index(metatile_index,
                                            data,
                                            Format.from_name('GTIFF'))
        return metatile


class TestHillShadingRenderNode(unittest.TestCase):

    def testRender(self):
        config = dict(
            prototype='node.hillshading',
            zfactor=1,
            scale=1,
            altitude=60,
            azimuth=45,
        )

        child_config = renderer.MetaTileRenderConfig('test_child')
        child = MockChildNode(child_config)
        node = renderer.RenderNodeFactory()('test', **config)
        node.add_child(child)

        metatile_index = create_metatile_index(2, 2, 3, stride=2)
        context = renderer.MetaTileContext(metatile_index, mode=renderer.MODE_DRYRUN)
        metatile = node.render(context)
        self.assertIsNotNone(metatile.data)


class TestColorReliefNode(unittest.TestCase):

    def testRender(self):
        config = dict(
            prototype='node.colorrelief',
            color_context='./input/hypsometric-map-world.txt',
        )

        child_config = renderer.MetaTileRenderConfig('test_child')
        child = MockChildNode(child_config)
        node = renderer.RenderNodeFactory()('test', **config)
        node.add_child(child)

        metatile_index = create_metatile_index(2, 2, 3, stride=2)
        context = renderer.MetaTileContext(metatile_index, mode=renderer.MODE_DRYRUN)
        metatile = node.render(context)
        self.assertIsNotNone(metatile.data)


class TestHomeBrewHillShadingNode(unittest.TestCase):

    def testRender(self):
        config = dict(
            prototype='node.homebrewhillshade',
            dataset_path=['./input/hailey.tif'],
            zfactor=1,
            scale=1,
            altitude=60,
            azimuth=45,
        )
        node = renderer.RenderNodeFactory()('test', **config)

        metatile_index = create_metatile_index(2, 2, 3, stride=2)
        context = renderer.MetaTileContext(metatile_index, mode=renderer.MODE_DRYRUN)
        metatile = node.render(context)
        self.assertIsNotNone(metatile.data)


class TestMapnikRenderNode(unittest.TestCase):

    def testRender(self):
        config = dict(
            prototype='node.mapnik',
            theme='./input/world.xml',
        )
        node = renderer.RenderNodeFactory()('test', **config)

        metatile_index = create_metatile_index(2, 2, 3, stride=2)
        context = renderer.MetaTileContext(metatile_index, mode=renderer.MODE_DRYRUN)
        metatile = node.render(context)
        self.assertIsNotNone(metatile.data)


class TestStorageNode(unittest.TestCase):

    def testRender(self):
        config = dict(
            prototype='node.storage',
            storage=dict(prototype='filesystem', root='/')
        )
        node = renderer.RenderNodeFactory()('test', **config)


class TestRasterNode(unittest.TestCase):

    def testRender(self):
        config = dict(
            prototype='node.raster',
            dataset_path='./input/hailey.tif'
        )
        node = renderer.RenderNodeFactory()('test', **config)

        metatile_index = create_metatile_index(2, 2, 3, stride=2)
        context = renderer.MetaTileContext(metatile_index, mode=renderer.MODE_DRYRUN)
        metatile = node.render(context)
        self.assertIsNotNone(metatile.data)


class TestImageMagicNode(unittest.TestCase):

    def testRender(self):
        config = dict(
            prototype='node.imagemagick',
            command='{{test_child_1}}',
            format='png'
        )

        child_config_1 = renderer.MetaTileRenderConfig('test_child_1')
        child_1 = MockChildNode(child_config_1)
        child_config_2 = renderer.MetaTileRenderConfig('test_child_2')
        child_2 = MockChildNode(child_config_2)

        node = renderer.RenderNodeFactory()('test', **config)
        node.add_child(child_1)
        node.add_child(child_2)

        metatile_index = create_metatile_index(2, 2, 3, stride=2)
        context = renderer.MetaTileContext(metatile_index, mode=renderer.MODE_DRYRUN)
        metatile = node.render(context)
        self.assertIsNotNone(metatile.data)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
