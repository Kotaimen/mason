# -*- coding:utf-8 -*-
'''
Base class of MetaTile renderer

Created on Sep 6, 2012
@author: ray
'''
from .datasource import MetaTileDataSource
from .processor import MetaTileProcessor
from .composer import MetaTileComposer


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

    def close(self):
        """ clean up resources """
        pass


class DataSourceRenderer(MetaTileRenderer):

    """ Simple MetaTile renderer

    return MetaTile from datasource
    """

    def __init__(self, datasource):
        assert isinstance(datasource, MetaTileDataSource)
        self._datasource = datasource

    def render(self, metatileindex):
        metatile = self._datasource.get(metatileindex)
        return metatile

    def close(self):
        self._datasource.close()


class ProcessingRenderer(MetaTileRenderer):

    """ Processing Renderer

    A processing renderer does some operations, eg. transform, translate,
    on a MetaTile which is taken from the source renderer.
    """

    def __init__(self, processor, source_renderer):
        assert isinstance(processor, MetaTileProcessor)
        assert isinstance(source_renderer, MetaTileRenderer)
        self._processor = processor
        self._source_renderer = source_renderer

    def render(self, metatileindex):
        metatile = self._source_renderer.render(metatileindex)
        metatile = self._processor.process(metatile)
        return metatile

    def close(self):
        self._processor.close()
        self._source_renderer.close()


class CompositeRenderer(MetaTileRenderer):

    """ Composite MetaTile renderer

    A composite MetaTile renderer compose a list of MetaTile collected
    from a list of other renderers.
    """

    def __init__(self, composer, source_renderers):
        assert isinstance(composer, MetaTileComposer)
        assert all(isinstance(s, MetaTileRenderer) for s in source_renderers)
        self._composer = composer
        self._source_renderer_list = list(source_renderers)

    def render(self, metatileindex):
        metatile_list = list()
        for source in self._source_renderer_list:
            metatile = source.render(metatileindex)
            metatile_list.append(metatile)

        metatile = self._composer.compose(metatile_list)
        return metatile

    def close(self):
        self._composer.close()
        for source in self._source_renderer_list:
            source.close()


class ConditionalRenderer(MetaTileRenderer):

    def __init__(self, condition, source_renderers):
        assert all(isinstance(s, MetaTileRenderer) for s in source_renderers)
        self._condition = condition
        self._source_renderers = source_renderers

    def render(self, metatileindex):
        zlevel = metatileindex.z
        renderer = self._source_renderers[self._condition[zlevel]]
        metatile = renderer.render(metatileindex)
        return metatile


class NullRenderer(MetaTileRenderer):

    """ Null renderer

    A special renderer always return None.
    """

    def render(self, metatileindex):
        return None
