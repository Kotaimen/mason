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

    def __init__(self, storage, renderer=None, work_mode='default', keep_cache=True):
        assert storage is not None
        self._renderer = renderer
        self._storage = storage
        self._work_mode = work_mode
        self.keep_cache = keep_cache

    def render(self, metatileindex):
        metatile = None
        if self._work_mode == 'dryrun':
            metatile = self._renderer.render(metatileindex)
        elif self._work_mode == 'readonly':
            metatile = self._storage.get(metatileindex)
        elif self._work_mode == 'overwrite':
            metatile = self._renderer.render(metatileindex)
            if metatile:
                self._storage.put(metatile)
        else:
            # default
            metatile = self._storage.get(metatileindex)
            if metatile:
                return metatile

            metatile = self._renderer.render(metatileindex)
            self._storage.put(metatile)

        return metatile

    def delete(self, metatileindex):
        self._storage.delete(metatileindex)
