# -*- coding:utf-8 -*-
'''
mason.renderer.persistent

Created on Mar 18, 2013
@author: ray
'''
from ..tilestorage import create_tilestorage


#===============================================================================
# Persistent
#===============================================================================
class RenderCache(object):

    """ Render Node Cache

    A cache configuration is a json object that specify
    where and how metatiles are cached.
    """

    def __init__(self, cache_cfg=None):
        cache_cfg = cache_cfg or dict(prototype='null')
        self._storage = create_tilestorage(**cache_cfg)

    def put(self, metatile):
        self._storage.put(metatile)

    def get(self, metatile_index):
        return self._storage.get(metatile_index)
