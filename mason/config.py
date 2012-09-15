# -*- coding:utf-8 -*-
'''
Renderer Configuration Parser

Created on Sep 10, 2012
@author: ray
'''
from .core import Pyramid, Metadata
from .renderer import (MetaTileDataSourceFactory,
                       MetaTileProcessorFactory,
                       MetaTileComposerFactory,
                       MetaTileRendererFactory,
                       CachedRenderer,
                       NullMetaTileRenderer
                       )
from .tilestorage import create_tilestorage


class RendererConfig(object):

    def __init__(self, config, pyramid, metadata):
        assert pyramid is not None
        assert metadata is not None
        self._pyramid = pyramid
        self._metadata = metadata

        self._name = config.pop('name', '')
        if not self._name:
            raise Exception('Renderer name is missing!')

        self._prototype = config.pop('prototype', None)
        if not self._prototype:
            raise Exception('Renderer prototype is missing!')

        self._sources = config.pop('sources', tuple())
        self._cache = config.pop('cache', None)
        self._params = config

    def to_renderer(self):
        raise NotImplementedError

    @staticmethod
    def from_prototpye(config, pyramid, metadata):
        prototype = config['prototype']

        if prototype.startswith('datasource'):
            return DataSourceRendererConfig(config, pyramid, metadata)
        elif prototype.startswith('processing'):
            return ProcessingRendererConfig(config, pyramid, metadata)
        elif prototype.startswith('composite'):
            return CompositeRendererConfig(config, pyramid, metadata)
        else:
            raise Exception('Unkonwn config prototype %s' % prototype)


class DataSourceRendererConfig(RendererConfig):

    RENDERER_REGISTRY = \
        {'datasource.mapnik': MetaTileDataSourceFactory.CARTO_MAPNIK,
         'datasource.postgis': MetaTileDataSourceFactory.CARTO_POSTGIS,
         'datasource.storage': None
        }

    def __init__(self, config, pyramid, metadata):
        RendererConfig.__init__(self, config, pyramid, metadata)
        assert self._prototype in self.RENDERER_REGISTRY
        assert not self._sources

        if self._prototype == 'datasource.storage':
            assert self._cache is not None

    def to_renderer(self):
        # datasource
        datasource_type = self.RENDERER_REGISTRY[self._prototype]
        if datasource_type:
            datasource = MetaTileDataSourceFactory(datasource_type,
                                                   **self._params
                                                   )
            # renderer
            renderer_type = MetaTileRendererFactory.DATASOURCE_RENDERER
            renderer = MetaTileRendererFactory(renderer_type,
                                               datasource=datasource)
        else:
            # null renderer
            renderer = NullMetaTileRenderer

        # attach cache
        if self._cache:
            storage = create_tilestorage(**self._cache)
            renderer = CachedRenderer(storage, renderer)

        return renderer


class ProcessingRendererConfig(RendererConfig):

    RENDERER_REGISTRY = \
        {'processing.hillshading': MetaTileProcessorFactory.GDAL_HILLSHADING,
         'processing.colorrelief': MetaTileProcessorFactory.GDAL_COLORRELIEF,
         'processing.rastertopng': MetaTileProcessorFactory.GDAL_RASTERTOPNG,
         'processing.fixmetadata': MetaTileProcessorFactory.GDAL_FIXMETADATA,
         'processing.warp': MetaTileProcessorFactory.GDAL_WARP,
        }

    def __init__(self, config, pyramid, metadata):
        RendererConfig.__init__(self, config, pyramid, metadata)
        assert self._prototype in self.RENDERER_REGISTRY
        assert len(self._sources) == 1

    def to_renderer(self):
        source_renderer = RendererConfig.from_prototpye(self._sources[0],
                                                        self._pyramid,
                                                        self._metadata
                                                        )

        # processor
        processor_type = self.RENDERER_REGISTRY[self._prototype]
        processor = MetaTileProcessorFactory(processor_type, **self._params)
        # renderer
        prototype = MetaTileRendererFactory.PROCESSING_RENDERER
        renderer = MetaTileRendererFactory(prototype,
                                           processor=processor,
                                           source_renderer=source_renderer,
                                           )

        # attach cache
        if self._cache:
            storage = create_tilestorage(**self._cache)
            renderer = CachedRenderer(storage, renderer)

        return renderer


class CompositeRendererConfig(RendererConfig):

    RENDERER_REGISTRY = \
        {'composite.imagemagick': MetaTileComposerFactory.IM,
         }

    def __init__(self, config, pyramid, metadata):
        RendererConfig.__init__(self, config, pyramid, metadata)
        assert self._prototype in self.RENDERER_REGISTRY
        assert len(self._sources) != 0

    def to_renderer(self):
        source_renderers = list()
        for source in self._sources:
            renderer_config = RendererConfig.from_prototpye(source,
                                                            self._pyramid,
                                                            self._metadata
                                                            )
            renderer = renderer_config.to_renderer()
            source_renderers.append(renderer)

        composer_type = self.RENDERER_REGISTRY[self._prototype]
        composer = MetaTileComposerFactory(composer_type, **self._params)

        prototype = MetaTileRendererFactory.COMPOSITE_RENDERER
        renderer = MetaTileRendererFactory(prototype,
                                           composer=composer,
                                           source_renderers=source_renderers,
                                           )
        # attach cache
        if self._cache:
            storage = create_tilestorage(**self._cache)
            renderer = CachedRenderer(storage, renderer)

        return renderer


class RenderRoot(object):

    def __init__(self,
                 pyramid_config,
                 metadata_config,
                 renderer_config,
                 renderer_cache_config=None,
                 ):
        self._pyramid = Pyramid(**pyramid_config)
        self._metadata = Metadata.make_metadata(**metadata_config)

        renderer_config = RendererConfig.from_prototpye(renderer_config,
                                                         self._pyramid,
                                                         self._metadata,
#                                                         renderer_cache_config
                                                         )
        self._renderer = renderer_config.to_renderer()

    @property
    def pyramid(self):
        return self._pyramid

    @property
    def metatile(self):
        return self._metadata

    @property
    def renderer(self):
        return self._renderer


class RenderConfigParser(object):

    def __init__(self, mode='default'):
        self._mode = mode

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

        # create render root
        mode = self._mode
        render_root = RenderRoot(pyramid_config,
                                 metadata_config,
                                 renderer_config,
                                 mode)

        return render_root


def create_render_tree_from_config(config_file, mode='default'):
    """ Create a render tree from given configuration file

    mode can be one of following:
    - default: write to cache after render
    - overwrite: render and overwrite any existing cache
    - readonly: only read from cache
    - dryrun: always render but does not write to cache
    """
    parser = RenderConfigParser(mode)
    return parser.parse(config_file)
