'''
Created on Mar 17, 2013

@author: ray
'''
import unittest
from mason.core.pyramid import Pyramid
from mason.renderer.node import *


def get_context():
    pyramid = Pyramid()
    metatile_index = pyramid.create_metatile_index(3, 2, 2, 2)
    with open('./input/hailey.tif', 'rb') as fp:
        data = fp.read()
    data_fmt = Format.GTIFF
    metatile = MetaTile.from_tile_index(metatile_index, data, data_fmt, 0)

    context = MetaTileContext(metatile_index)
    key = 'elev' + repr(metatile_index)
    context.source_pool.put(key, metatile)
    return context


class HillShadingRenderNodeTest(unittest.TestCase):

    def setUp(self):
        self._context = get_context()

    def tearDown(self):
        pass

    def testName(self):
        render_node = HillShadingRenderNode('dummy', source_names=['elev'])
        self.assertEqual(render_node.name, 'dummy')

    def testRender(self):
        render_node = HillShadingRenderNode('dummy', source_names=['elev'])
        metatile = render_node.render(self._context)
        self.assertIsNotNone(metatile.data)

    def testLambda(self):
        render_node = HillShadingRenderNode('dummy', source_names=['elev'],
                                            zfactor=lambda z, x, y: 1,
                                            scale=lambda z, x, y: 1,
                                            altitude=lambda z, x, y: 45,
                                            azimuth=lambda z, x, y: 315)
        metatile = render_node.render(self._context)
        self.assertIsNotNone(metatile.data)


class ColorReliefRenderNodeTest(unittest.TestCase):

    def setUp(self):
        self._context = get_context()
        self._color_context = './input/hypsometric-map-world.txt'

    def tearDown(self):
        pass

    def testName(self):
        render_node = ColorReliefRenderNode('dummy',
                                            ['elev'],
                                            self._color_context)
        self.assertEqual(render_node.name, 'dummy')

    def testRender(self):
        render_node = ColorReliefRenderNode('dummy',
                                            ['elev'],
                                            self._color_context)
        metatile = render_node.render(self._context)
        self.assertIsNotNone(metatile.data)


class StorageRenderNodeTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testName(self):
        pass

    def testRender(self):
        pass


class MapnikRenderNodeTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testName(self):
        pass

    def testRender(self):
        pass


class RasterRenderNodeTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testName(self):
        pass

    def testRender(self):
        pass

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
