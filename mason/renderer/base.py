# -*- coding:utf-8 -*-
'''
Render node of a render tree

Created on Sep 6, 2012
@author: ray
'''


#==============================================================================
# Base class of MetaTile renderer
#==============================================================================
class MetaTileRenderer(object):

    """ Base class of MetaTile renderer

    return a MetaTile according to the MetaTile index.
    """

    def render(self, metatileindex):
        """ render a MetaTile, return None if not found """
        raise NotImplementedError


class ProcessingMetaTileRenderer(MetaTileRenderer):

    """ Processing Renderer

    A processing renderer does some operations, eg. transform, translate,
    on a MetaTile which is taken from the source renderer.
    """

    def __init__(self, source_renderer):
        self._source_renderer = source_renderer

    def _process(self, metatile):
        raise NotImplementedError

    def render(self, metatileindex):
        metatile = self._source.render(metatileindex)
        metatile = self._process(metatile)
        return metatile


class CompositeMetaTileRenderer(MetaTileRenderer):

    """ Composite MetaTile renderer

    A composite MetaTile renderer compose a list of MetaTile collected
    from a list of other renderers.
    """

    def __init__(self, *source_renderers):
        self._source_renderer_list = list(source_renderers)

    def _compose(self, metatile_list):
        raise NotImplementedError

    def render(self, metatileindex):
        metatile_list = list()
        for source in self._sources:
            metatile = source.render(metatileindex)
            metatile_list.append(metatile)

        metatile = self._compose(metatile_list)
        return metatile
