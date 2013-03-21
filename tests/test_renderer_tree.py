# -*- coding:utf-8 -*-
'''
test_renderer_tree

Created on Mar 16, 2013
@author: ray
'''
import unittest
from mason.renderer.tree import RenderContext, RenderNode


class DummyContext(RenderContext):

    def __str__(self):
        return self.__class__.__name__


class DummyRenderNode(RenderNode):

    def __render__(self, context, sources):
        result = self._name
        if sources:
            result = ':'.join((self._name, '&'.join(sources.values())))
        return result


class TestRenderNode(unittest.TestCase):

    def testName(self):
        node = DummyRenderNode('dummy')
        self.assertEqual(node.name, 'dummy')

    def testAddNode(self):
        node = DummyRenderNode('dummy')
        child = DummyRenderNode('child')
        node.add_child(child)

        context = DummyContext()
        self.assertEqual(node.render(context), 'dummy:child')

    def testRender(self):
        root = DummyRenderNode('root')
        child1 = DummyRenderNode('child1')
        child2 = DummyRenderNode('child2')
        child3 = DummyRenderNode('child3')

        root.add_child(child1)
        root.add_child(child2)

        child1.add_child(child3)

        context = DummyContext()
        self.assertEqual(root.render(context), 'root:child1:child3&child2')

    def testRepr(self):
        node = DummyRenderNode('dummy')
        self.assertEqual(repr(node), "DummyRenderNode('dummy')")


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
