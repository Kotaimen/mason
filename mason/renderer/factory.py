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

    def __call__(self, prototype, name, source_names,):
        pass




