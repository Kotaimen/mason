# -*- coding:utf-8 -*-
'''
Renderer Configuration Parser

Created on Sep 10, 2012
@author: ray
'''
from .core import Pyramid, Metadata, Format, metatile_fission
from .renderer import (
                       MetaTileDataSourceFactory,
                       MetaTileProcessorFactory,
                       MetaTileComposerFactory,
                       MetaTileRendererFactory,
                       CachedRenderer,
                       NullMetaTileRenderer
                       )
from .tilestorage import create_tilestorage


#==============================================================================
# Create cached renderer
#==============================================================================
def build_cache_storage(cache_config, pyramid, metadata):
    """ create cache storage from cache configuration """
    if not cache_config:
        cache_config = dict(prototype='null')

    prototype = cache_config.pop('prototype', None)
    if not prototype:
        raise ValueError('storage prototype is missing.')

    storage = create_tilestorage(\
                   prototype,
                   pyramid,
                   metadata,
                   **cache_config
                   )

    return storage


#==============================================================================
# Renderer Configuration
#==============================================================================
class RendererConfig(object):

    """ Base class of renderer configuration """

    def __init__(self, renderer_config):
        """ get information """
        self._name = renderer_config.pop('name', None)
        self._prototype = renderer_config.pop('prototype', None)
        self._sources = renderer_config.pop('sources', tuple())
        self._cache = renderer_config.pop('cache', None)
        self._params = renderer_config

        if not self._name:
            raise Exception('renderer name is missing or invalid!')

        if not self._prototype:
            raise Exception('renderer prototype is missing or invalid!')

    def to_renderer(self, pyramid, metadata, work_mode):
        """ create renderer """
        raise NotImplementedError

    @staticmethod
    def from_dict(config):
        """ renderer configuration factory"""
        prototype, _ = config['prototype'].split('.')

        if prototype == 'datasource':
            return DataSourceRendererConfig(config)
        elif prototype == 'processing':
            return ProcessingRendererConfig(config)
        elif prototype == 'composite':
            return CompositeRendererConfig(config)
        else:
            raise Exception('Unknown renderer prototype %s' % prototype)


class DataSourceRendererConfig(RendererConfig):

    """ DataSource Renderer Configuration

    example:

        {
            'name':         'test',
            'prototype':    'datasource.*****'
            'cache':        None,

            'param_1':      1,
            'param_2':      2,
            'param_3':      3,
        }
    """

    RENDERER_REGISTRY = \
        {
         'datasource.mapnik': MetaTileDataSourceFactory.CARTO_MAPNIK,
         'datasource.postgis': MetaTileDataSourceFactory.CARTO_POSTGIS,
         'datasource.storage': None
        }

    def __init__(self, renderer_config):
        RendererConfig.__init__(self, renderer_config)

        # check prototype
        if self._prototype not in self.RENDERER_REGISTRY:
            raise ValueError('unknown datasource %s' % self._prototype)

        if self._prototype == 'datasource.storage' and self._cache is None:
            raise ValueError('datasource.storage needs cache.')

        # check sources
        if self._sources:
            raise ValueError("datasource renderer don't need source renderer.")

    def to_renderer(self, pyramid, metadata, work_mode):
        # renderer
        source_type = self.RENDERER_REGISTRY[self._prototype]
        if source_type:
            datasource = MetaTileDataSourceFactory(source_type, **self._params)
            renderer = MetaTileRendererFactory(
                               MetaTileRendererFactory.DATASOURCE_RENDERER,
                               datasource=datasource
                               )
        else:
            renderer = NullMetaTileRenderer

        # attach cache
        storage = build_cache_storage(self._cache, pyramid, metadata)
        renderer = CachedRenderer(storage, renderer, work_mode)
        return renderer


class ProcessingRendererConfig(RendererConfig):

    """ Processing Renderer Configuration

    example:

        {
            'name':         'test',
            'prototype':    'processing.*****'
            'sources':      (source1,)
            'cache':        None,

            'param_1':      1,
            'param_2':      2,
            'param_3':      3,
        }
    """

    RENDERER_REGISTRY = \
        {
         'processing.hillshading': MetaTileProcessorFactory.GDAL_HILLSHADING,
         'processing.colorrelief': MetaTileProcessorFactory.GDAL_COLORRELIEF,
         'processing.rastertopng': MetaTileProcessorFactory.GDAL_RASTERTOPNG,
         'processing.fixmetadata': MetaTileProcessorFactory.GDAL_FIXMETADATA,
         'processing.warp': MetaTileProcessorFactory.GDAL_WARP,
        }

    def __init__(self, renderer_config):
        RendererConfig.__init__(self, renderer_config)

        # check prototype
        if self._prototype not in self.RENDERER_REGISTRY:
            raise ValueError('unknown processing  %s' % self._prototype)

        # check sources
        if not len(self._sources) == 1:
            raise ValueError('processing renderer need one source renderer.')

    def to_renderer(self, pyramid, metadata, work_mode):

        # processor
        processor_type = self.RENDERER_REGISTRY[self._prototype]
        processor = MetaTileProcessorFactory(processor_type, **self._params)

        # source renderer
        config = RendererConfig.from_dict(self._sources[0])
        source_renderer = config.to_renderer(pyramid, metadata, work_mode)

        # renderer
        renderer = MetaTileRendererFactory(
                       MetaTileRendererFactory.PROCESSING_RENDERER,
                       processor=processor,
                       source_renderer=source_renderer,
                       )

        # attach cache
        storage = build_cache_storage(self._cache, pyramid, metadata)
        renderer = CachedRenderer(storage, renderer, work_mode)

        return renderer


class CompositeRendererConfig(RendererConfig):

    """ Composite Renderer Configuration

    example:

        {
            'name':         'test',
            'prototype':    'composite.*****'
            'sources':      (source1, source2, ...)
            'cache':        None,

            'param_1':      1,
            'param_2':      2,
            'param_3':      3,
        }
    """

    RENDERER_REGISTRY = \
        {
         'composite.imagemagick': MetaTileComposerFactory.IM,
        }

    def __init__(self, renderer_config):
        RendererConfig.__init__(self, renderer_config)

        # check prototype
        if self._prototype not in self.RENDERER_REGISTRY:
            raise ValueError('unknown composite %s' % self._prototype)

        # check sources
        if not len(self._sources) >= 1:
            raise ValueError('composite renderer need 1+ source renderer.')

    def to_renderer(self, pyramid, metadata, work_mode):

        # create sources
        source_renderers = list()
        for source in self._sources:
            config = RendererConfig.from_dict(source)
            renderer = config.to_renderer(pyramid, metadata, work_mode)
            source_renderers.append(renderer)

        # renderer
        composer_type = self.RENDERER_REGISTRY[self._prototype]
        composer = MetaTileComposerFactory(composer_type, **self._params)
        renderer = MetaTileRendererFactory(
                       MetaTileRendererFactory.COMPOSITE_RENDERER,
                       composer=composer,
                       source_renderers=source_renderers,
                       )

        # attach cache
        storage = build_cache_storage(self._cache, pyramid, metadata)
        renderer = CachedRenderer(storage, renderer, work_mode)

        return renderer


#==============================================================================
# Render Root
#==============================================================================
class RenderRoot(object):

    """ Root of the renderer tree """

    def __init__(self,
                 pyramid_config=None,
                 metadata_config=None,
                 renderer_config=None,
                 cache_config=None,
                 work_mode='default',
                 ):

        if 'format' in pyramid_config:
            format_name = pyramid_config['format']
            pyramid_config['format'] = Format.from_name(format_name)

        self._pyramid = Pyramid(**pyramid_config)
        self._metadata = Metadata.make_metadata(**metadata_config)
        self._work_mode = work_mode

        config = RendererConfig.from_dict(renderer_config)
        self._renderer = config.to_renderer(self._pyramid,
                                            self._metadata,
                                            self._work_mode)

        self._cache = build_cache_storage(cache_config,
                                          self._pyramid,
                                          self._metadata)

    @property
    def pyramid(self):
        return self._pyramid

    @property
    def metadata(self):
        return self._metadata

    @property
    def renderer(self):
        return self._renderer

    def render(self, metatile_index):
        metatile = self._renderer.render(metatile_index)
        if self._cache and self._work_mode in ['default', 'overwrite']:
            tiles = metatile_fission(metatile)
            self._cache.put_multi(tiles)
        return metatile


#==============================================================================
# Configuration Parser
#==============================================================================
class RenderConfigParser(object):

    def __init__(self, work_mode='default'):
        if work_mode not in ['default', 'overwrite', 'readonly', 'dryrun']:
            raise ValueError('Unknown work mode %s' % work_mode)
        self._work_mode = work_mode

    def parse(self, config_file):
        global_vars, local_vars = {}, {}
        execfile(config_file, global_vars, local_vars)

        render_config = local_vars['ROOT']

        # get pyramid configuration
        pyramid_config = render_config.get('pyramid', None)
        if pyramid_config is None:
            raise Exception('Pyramid Configuration is missing!')

        # get metadata configuration
        metadata_config = render_config.get('metadata', None)
        if metadata_config is None:
            raise Exception('Metadata Configuration is missing!')

        # get renderer configuration
        renderer_config = render_config.get('renderer', None)
        if not renderer_config:
            raise Exception('Renderer Configuration is missing!')

        cache_config = render_config.get('cache', None)

        # create render root
        render_root = RenderRoot(pyramid_config,
                                 metadata_config,
                                 renderer_config,
                                 cache_config,
                                 self._work_mode
                                 )

        return render_root


#==============================================================================
# Facade
#==============================================================================
def create_render_tree_from_config(config_file, mode='default'):
    """ Create a render tree from given configuration file.

    mode can be one of following:
    - default: write to cache after render
    - overwrite: render and overwrite any existing cache
    - readonly: only read from cache
    - dryrun: always render but does not write to cache
    """
    parser = RenderConfigParser(mode)
    return parser.parse(config_file)
