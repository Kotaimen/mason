# -*- coding:utf-8 -*-
'''
mason.renderer.persistent

Created on Mar 18, 2013
@author: ray
'''


#===============================================================================
# Persistent
#===============================================================================
class RenderCache(object):

    """ Render Node Cache

    A cache configuration is a json object that specify
    where and how metatiles are cached.
    """

    def __init__(self, cache=None):
        self._cache = cache

    def put(self, metatile):
        self._cache and self._cache.put(metatile)

    def get(self, metatile_index):
        return self._cache and self._cache.get(metatile_index)

    def delete(self, metatile_index):
        self._cache and self._cache.delete(metatile_index)
