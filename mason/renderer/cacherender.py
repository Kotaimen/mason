# -*- coding:utf-8 -*-
'''
Cached MetaTile Render

Created on Sep 6, 2012
@author: ray
'''
from .renderer import MetaTileRenderer


class CachedRenderer(MetaTileRenderer):

    """ Cache renderer

    A Cache renderer is an ancillary renderer which caches the result
    of another render.
    """

    def __init__(self, storage, renderer=None, overwrite=False):
        self._renderer = renderer
        self._storage = storage
        self._overwrite = overwrite

    def render(self, metatileindex):

        if not self._overwrite:
            metatile = self._storage.get(metatileindex)
            if metatile:
                return metatile

        metatile = self._renderer.render(metatileindex)
        self._storage.put(metatile)

        return metatile
