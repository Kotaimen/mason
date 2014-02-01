# -*- coding:utf-8 -*-
'''
MetaTile renderer factory

Created on Sep 10, 2012
@author: ray
'''
from .node import (MetaTileContext,
                   MetaTileRenderNode,
                   HillShadingRenderNode,
                   ColorReliefRenderNode,
                   StorageRenderNode,
                   MapnikRenderNode,
                   RasterRenderNode,
                   ImageMagicRenderNode,
                   HomeBrewHillShade,
                   Brick2RenderNode,
                   )


class RenderNodeFactory(object):

    REGISTRY = {
                'node.null': MetaTileRenderNode,
                'node.hillshading': HillShadingRenderNode,
                'node.colorrelief': ColorReliefRenderNode,
                'node.storage': StorageRenderNode,
                'node.mapnik': MapnikRenderNode,
                'node.raster': RasterRenderNode,
                'node.imagemagick': ImageMagicRenderNode,
                'node.homebrewhillshade': HomeBrewHillShade,
                'node.brick2': Brick2RenderNode,
                }

    def __call__(self, prototype, name, cache=None, **params):
        klass = self.REGISTRY.get(prototype)
        if not klass:
            raise RuntimeError('Unknown render node "%s" !' % prototype)

        render_node = klass(name, cache=cache, **params)
        return render_node


def create_render_node(prototype, name, cache=None, **params):
    return RenderNodeFactory()(prototype, name, cache=cache, **params)
