# -*- coding:utf-8 -*-
'''
MetaTile renderer factory

Created on Sep 10, 2012
@author: ray
'''
from ..cartographer import CartographerFactory, GDALProcessorFactory
from ..composer import ImageMagickComposer
from ..tilestorage import attach_tilestorage
from .datasource import (CartographerMetaTileDataSource,
                         StorageMetaTileDataSource
                         )
from .processor import GDALMetaTileProcessor
from .composer import ImageMagicMetaTileComposer
from .renderer import (DataSourceRenderer,
                       ProcessingRenderer,
                       CompositeRenderer,
                       ConditionalRenderer
                       )
from .cacherender import CachedRenderer


#==============================================================================
# Renderer Factories
#==============================================================================
class _DataSourceRendererFactory(object):

    """ DataSource Renderer Factory

    Create a datasource renderer with a given prototype.
    Mapnik, PostGIS, and Storage is supported now.
    """

    DATASOURCE_REGISTRY = ['mapnik', 'postgis', 'storage', 'dataset']

    def __call__(self, prototype, **params):
        params = dict(params)
        if prototype == 'storage':
            # to avoid using the same parameter name 'prototype'
            prototype = params.pop('storage_type', None)
            if not prototype:
                raise RuntimeError('Please provide the storage_type of the '
                'storage to be attached.')
            default = params.pop('default', None)

            storage = attach_tilestorage(prototype, **params)
            metatile_datasource = StorageMetaTileDataSource(storage, default)
        elif prototype in self.DATASOURCE_REGISTRY:
            carto = CartographerFactory(prototype, **params)
            metatile_datasource = CartographerMetaTileDataSource(carto)

        else:
            raise RuntimeError('Unknown prototype %s' % prototype)

        return DataSourceRenderer(metatile_datasource)


class _ProcessingRendererFactory(object):

    """ Processing Renderer Factory

    Create a processing renderer with a given prototype.
    Gdal processing is supported, including hillshading,
    colorrelief, converting raster to PNG, fixing metatdata
    and warping spatial reference system.
    """

    PROCESSING_REGISTRY = ['hillshading',
                           'colorrelief',
                           'rastertopng',
                           'fixmetadata',
                           'warp',
                           ]

    def __call__(self, prototype, source, **params):
        params = dict(params)
        if prototype in self.PROCESSING_REGISTRY:
            gdaltool = GDALProcessorFactory(prototype, **params)
            metatile_processor = GDALMetaTileProcessor(gdaltool)

        else:
            raise RuntimeError('Unknown prototype %s' % prototype)

        return ProcessingRenderer(metatile_processor, source)


class _CompositeRendererFactory(object):

    """ Composite Renderer Factory

    Create a composite renderer by given prototype and parameters.
    Imagemagick composer is supported now.
    """

    COMPOSITE_REGISTRY = ['imagemagick', 'selector']

    def __call__(self, prototype, source_list, **params):
        params = dict(params)
        if prototype == 'imagemagick':
            # params: format, command
            composer = ImageMagickComposer(**params)
            metatile_composer = ImageMagicMetaTileComposer(composer)
            return CompositeRenderer(metatile_composer, source_list)
        elif prototype == 'selector':
            condition = params.pop('condition', None)
            if not condition:
                raise RuntimeError('no condition specified.')
            if len(condition) == len(source_list):
                raise RuntimeError('condition and sources does not match.')

            return ConditionalRenderer(condition, source_list)
        else:
            raise RuntimeError('Unknown prototype %s' % prototype)


class RendererFactory(object):

    DataSourceRendererFactory = _DataSourceRendererFactory()
    ProcessingRendererFactory = _ProcessingRendererFactory()
    CompositeRendererFactory = _CompositeRendererFactory()

    def __init__(self, mode='default'):
        self._mode = mode

    def __call__(self, prototype, sources, storage, **attr):
        try:
            major, minor = prototype.split('.')
        except Exception:
            raise RuntimeError('unknown prototype "%s"' % prototype)

        factory = None
        if major == 'datasource':
            factory = self.DataSourceRendererFactory
            renderer = factory(minor, **attr)
        elif major == 'processing':
            factory = self.ProcessingRendererFactory
            if len(sources) != 1:
                raise RuntimeError('processor only accept one source')
            renderer = factory(minor, sources[0], **attr)
        elif major == 'composite':
            factory = self.CompositeRendererFactory
            if len(sources) < 1:
                raise RuntimeError('composite need one or more sources')
            renderer = factory(minor, sources, **attr)
        else:
            raise RuntimeError('Unknown prototype %s' % prototype)

        if storage:
            renderer = CachedRenderer(storage, renderer, work_mode=self._mode)

        return renderer
