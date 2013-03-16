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

    def __init__(self, name, source_names=[]):
        RenderNode.__init__(self, name, source_names)

    def __render__(self, context, sources):
        return str(context)


class TestRenderNode(unittest.TestCase):

    def testName(self):
        node = DummyRenderNode('dummy')
        self.assertEqual(node.name, 'dummy')

    def testRender(self):
        node = DummyRenderNode('dummy')
        context = DummyContext()
        self.assertEqual(node.render(context), 'DummyContext')
        self.assertEqual(context.source_pool.get('dummy'), 'DummyContext')

    def testRepr(self):
        node = DummyRenderNode('dummy')
        self.assertEqual(repr(node), "DummyRenderNode('dummy')")


class TestRenderTree(unittest.TestCase):

    def testAddNode(self):
        pass

    def testRender(self):
        pass


