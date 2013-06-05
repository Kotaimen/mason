'''
Created on Jun 4, 2013

@author: ray
'''
import unittest
from mason import renderer


class MockRenderContext(renderer.RenderContext):

    @property
    def content(self):
        return 100;


class MockRenderNode(renderer.RenderNode):

    def render(self, context):
        summary = 0
        for child in self.children:
            summary += 2 * child.render(context)
        return summary + context.content


class TestRenderNode(unittest.TestCase):

    def setUp(self):
        self._node = MockRenderNode('test')

    def tearDown(self):
        self._node.close()

    def testName(self):
        self.assertEqual(self._node.name, 'test')

    def testAddChild(self):
        child1 = MockRenderNode('child1')
        child2 = MockRenderNode('child2')
        self._node.add_child(child1)
        self._node.add_child(child2)

        self.assertListEqual(self._node.children, [child1, child2])

    def testRender(self):
        context = MockRenderContext()
        self.assertEqual(self._node.render(context), 100)

        child1 = MockRenderNode('child1')
        child2 = MockRenderNode('child2')
        self._node.add_child(child1)
        self._node.add_child(child2)
        self.assertEqual(self._node.render(context), 500)

        child3 = MockRenderNode('child3')
        child2.add_child(child3)
        self.assertEqual(self._node.render(context), 900)

    def testRepr(self):
        self.assertEqual(repr(self._node), "MockRenderNode('test')")


class TestNullRenderNode(unittest.TestCase):

    def setUp(self):
        self._node = renderer.NullRenderNode('null')

    def tearDown(self):
        self._node.close()

    def testRender(self):
        context = MockRenderContext()
        self.assertIsNone(self._node.render(context))


class MockMetaTileIndex(object):

    def __init__(self, z, x, y):
        self._coord = (z, x, y)

    @property
    def coord(self):
        return self._coord


class MockMetaTile(object):

    def __init__(self, index, data):
        self._index = index
        self._data = data

    @property
    def index(self):
        return self._index

    @property
    def data(self):
        return self._data


class MockCache(object):

    def __init__(self):
        self._cache = dict()

    def put(self, metatile):
        self._cache[metatile.index] = metatile

    def get(self, metatile_index):
        return self._cache.get(metatile_index, None)


class MockMetaTileRenderNode(renderer.MetaTileRenderNode):

    def _render_impl(self, context, source_nodes):
        summary = 0
        for node in source_nodes:
            summary += 2 * node.render(context)

        metatile_index = context.metatile_index
        data = summary + 100
        metatile = MockMetaTile(metatile_index, data)
        return metatile


class TestMetaTileRenderNode(unittest.TestCase):

    def setUp(self):
        cache = MockCache()
        keep_cache = False
        config = renderer.MetaTileRenderConfig('test', cache, keep_cache)
        self._node = MockMetaTileRenderNode(config)
        self._cache = cache

    def tearDown(self):
        self._node.close()

    def testReadOnlyRender(self):
        mode = renderer.MODE_READONLY
        metatile_index = MockMetaTileIndex(2, 2, 3)
        context = renderer.MetaTileContext(metatile_index, mode)
        metatile = self._node.render(context)
        self.assertIsNone(metatile)
        self.assertIsNone(self._cache.get(metatile_index))

        metatile = MockMetaTile(metatile_index, data=100)
        self._cache.put(metatile)
        metatile = self._node.render(context)
        self.assertEqual(metatile.data, 100)

    def testDryRunRender(self):
        mode = renderer.MODE_DRYRUN
        metatile_index = MockMetaTileIndex(2, 2, 3)
        context = renderer.MetaTileContext(metatile_index, mode)
        metatile = self._node.render(context)
        self.assertEqual(metatile.data, 100)
        self.assertIsNone(self._cache.get(metatile_index))

    def testHybridRender(self):
        mode = renderer.MODE_HYBRID
        metatile_index = MockMetaTileIndex(2, 2, 3)
        context = renderer.MetaTileContext(metatile_index, mode)
        metatile = self._node.render(context)
        self.assertEqual(metatile.data, 100)
        self.assertEqual(self._cache.get(metatile_index), metatile)

    def testOverwriteRender(self):
        mode = renderer.MODE_OVERWRITE
        metatile_index = MockMetaTileIndex(2, 2, 3)
        context = renderer.MetaTileContext(metatile_index, mode)
        metatile = self._node.render(context)
        self.assertEqual(metatile.data, 100)
        self.assertEqual(self._cache.get(metatile_index), metatile)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
