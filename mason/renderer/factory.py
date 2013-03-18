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

    REGISTRY = dict(hillshading=HillShadingRenderNode,
                    colorrelief=ColorReliefRenderNode,
                    storage=StorageRenderNode,
                    mapnik=MapnikRenderNode,
                    raster=RasterRenderNode,
                    imagemagic=ImageMagicRenderNode
                    )

    def __call__(self, prototype, name, source_names, **params):
        klass = self.REGISTRY.get(prototype)
        if not klass:
            raise RuntimeError('RenderNode %s not found!' % prototype)

        render_node = klass(name, source_names, **params)
        return render_node
