# -*- coding:utf-8 -*-
'''
Render Node

Created on March 14, 2013
@author: ray
'''


#===============================================================================
# Render Context Base Class
#===============================================================================
class RenderContext(object):
    pass


#===============================================================================
# Render Node Base Class
#===============================================================================
class RenderNode(object):

    def __init__(self, name):
        self._name = name
        self._children = list()

    @property
    def name(self):
        return self._name

    @property
    def children(self):
        return self._children

    def add_child(self, node):
        self._children.append(node)

    def render(self, context):
        raise NotImplementedError

    def close(self):
        pass

    def __repr__(self):
        return "%s('%s')" % (self.__class__.__name__, self._name)


class NullRenderNode(RenderNode):

    def render(self, context):
        return None


#===============================================================================
# MetaTile Render Mode
#===============================================================================
MODE_READONLY = 'readonly'
MODE_HYBRID = 'hybrid'
MODE_OVERWRITE = 'overwrite'
MODE_DRYRUN = 'dryrun'


#===============================================================================
# MetaTile Context
#===============================================================================
class MetaTileContext(object):

    def __init__(self, metatile_index, mode=MODE_READONLY):
        self._metatile_index = metatile_index
        self._mode = mode

    @property
    def metatile_index(self):
        return self._metatile_index

    @property
    def mode(self):
        return self._mode


#===============================================================================
# MetaTile Render Config
#===============================================================================
class MetaTileRenderConfig(object):

    def __init__(self, name, cache=None, keep_cache=False, **kwargs):
        self._name = name
        self._cache = cache
        self._keep_cache = keep_cache
        self._params = kwargs

    @property
    def name(self):
        return self._name

    @property
    def cache(self):
        return self._cache

    @property
    def keep_cache(self):
        return self._keep_cache

    def get_params_from_context(self, context):
        return self._params


#===============================================================================
# MetaTile Render Node (Base)
#===============================================================================
class MetaTileRenderNode(RenderNode):

    def __init__(self, config):
        assert isinstance(config, MetaTileRenderConfig)
        RenderNode.__init__(self, config.name)
        self._cache = config.cache
        self._keep_cache = config.keep_cache

    def render(self, context):
        assert isinstance(context, MetaTileContext)

        mode = context.mode
        metatile_index = context.metatile_index

        # get from cache
        if self._cache is not None and mode in (MODE_READONLY, MODE_HYBRID):
            metatile = self._cache.get(metatile_index)
            if metatile is not None or mode == MODE_READONLY:
                return metatile

        # render
        metatile = self._render_impl(context, self.children)

        # put into cache
        if self._cache is not None and metatile is not None \
            and mode in (MODE_OVERWRITE, MODE_HYBRID):
            self._cache.put(metatile)

        return metatile

    def erase(self, context):
        for child in self._children:
            child.erase(context)

        if not self._keep_cache:
            metatile_index = context.metatile_index
            self._cache.delete(metatile_index)

    def close(self):
        pass

    def _render_impl(self, context, source_nodes):
        raise NotImplementedError
