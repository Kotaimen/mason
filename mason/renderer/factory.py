# -*- coding:utf-8 -*-
'''
MetaTile renderer factory

Created on Sep 10, 2012
@author: ray
'''
from .node import (MetaTileContext,
                   HillShadingRenderNode,
                   ColorReliefRenderNode,
                   StorageRenderNode,
                   MapnikRenderNode,
                   RasterRenderNode,
                   ImageMagicRenderNode)


class RenderNodeFactory(object):

    REGISTRY = {
                'node.hillshading': HillShadingRenderNode,
                'node.colorrelief': ColorReliefRenderNode,
                'node.storage': StorageRenderNode,
                'node.mapnik': MapnikRenderNode,
                'node.raster': RasterRenderNode,
                'node.imagemagick': ImageMagicRenderNode
                }

    def __call__(self, prototype, name, cache=None, **params):
        klass = self.REGISTRY.get(prototype)
        if not klass:
            raise RuntimeError('Unknown render node "%s" !' % prototype)

        render_node = klass(name, cache=cache, **params)
        return render_node


def create_render_node(prototype, name, cache=None, **params):
    return RenderNodeFactory()(prototype, name, cache=cache, **params)
