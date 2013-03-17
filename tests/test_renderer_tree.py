# -*- coding:utf-8 -*-
'''
test_renderer_tree

Created on Mar 16, 2013
@author: ray
'''
import unittest
from mason.renderer.tree import RenderContext, RenderNode, RenderTree
from mason.renderer.tree import UnknownParentNode, MissingSource


class DummyContext(RenderContext):

    def __str__(self):
        return self.__class__.__name__


class DummyRenderNode(RenderNode):

    def __init__(self, name, source_names=[]):
        RenderNode.__init__(self, name, source_names)

    def render(self, context):
        pool = context.source_pool

        sources = list()
        for name in self._source_names:
            source = pool.get(name)
            if not source:
                raise MissingSource(name)
            sources.append(source)

        result = self._name
        if sources:
            result = ':'.join((self._name, '&'.join(sources)))
        pool.put(self._name, result)
        return result


class TestRenderNode(unittest.TestCase):

    def testName(self):
        node = DummyRenderNode('dummy')
        self.assertEqual(node.name, 'dummy')

    def testRender(self):
        node = DummyRenderNode('dummy')
        context = DummyContext()
        self.assertEqual(node.render(context), 'dummy')
        self.assertEqual(context.source_pool.get('dummy'), 'dummy')

        node = DummyRenderNode('dummy', source_names=['wrong'])
        context = DummyContext()
        self.assertRaises(MissingSource, node.render, context)

    def testRepr(self):
        node = DummyRenderNode('dummy')
        self.assertEqual(repr(node), "DummyRenderNode('dummy')")


class TestRenderTree(unittest.TestCase):

    def testAddNode(self):
        root = DummyRenderNode('root')
        tree = RenderTree(root)

        node = DummyRenderNode('dummy')
        self.assertRaises(UnknownParentNode, tree.add_node, node, 'wrong')

        self.assertEqual(tree.add_node(node, 'root'), node)

    def testRender(self):
        root = DummyRenderNode('root', ['dummy1'])
        tree = RenderTree(root)

        node1 = DummyRenderNode('dummy1', ['dummy2'])
        tree.add_node(node1, 'root')

        node2 = DummyRenderNode('dummy2')
        tree.add_node(node2, 'dummy1')

        context = DummyContext()
        self.assertEqual(tree.render(context), 'root:dummy1:dummy2')

    def testClose(self):
        root = DummyRenderNode('root', ['dummy1'])
        tree = RenderTree(root)
        tree.close()


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
