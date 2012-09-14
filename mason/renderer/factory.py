# -*- coding:utf-8 -*-
'''
MetaTile renderer factory

Created on Sep 10, 2012
@author: ray
'''
from ..cartographer import CartographerFactory, GDALProcessorFactory
from .datasource import CartographerMetaTileDataSource
from .processor import GDALMetaTileProcessor
from .composer import ImageMagicMetaTileComposer
from .renderer import (DataSourceMetaTileRenderer,
                       ProcessingMetaTileRenderer,
                       CompositeMetaTileRenderer,
                       )


#==============================================================================
# Base class of Factory
#==============================================================================
class _Factory(object):

    def __call__(self, klass_type, **params):
        raise NotImplementedError


#==============================================================================
# DataSource Factory
#==============================================================================
def create_carto_mapnik(**params):
    carto = CartographerFactory('mapnik', **params)
    return CartographerMetaTileDataSource(carto)


def create_carto_postgis(**params):
    carto = CartographerFactory('postgis', **params)
    return CartographerMetaTileDataSource(carto)


class _MetaTileDataSourceFactory(_Factory):

    CARTO_MAPNIK = 'cartographer_mapnik'
    CARTO_POSTGIS = 'cartographer_postgis'

    DATASOURCE_REGISTRY = {CARTO_MAPNIK: create_carto_mapnik,
                           CARTO_POSTGIS: create_carto_postgis,
                           }

    def __call__(self, prototype, **params):
        creator = self.DATASOURCE_REGISTRY.get(prototype, None)
        if not creator:
            raise RuntimeError('Unsupported type %s' % prototype)
        return creator(**params)


#==============================================================================
# Processor Factory
#==============================================================================
def create_gdal_hillshading_processor(**params):
    processor = GDALProcessorFactory('hillshading', **params)
    return GDALMetaTileProcessor(processor)


def create_gdal_colorrelief_processor(**params):
    processor = GDALProcessorFactory('colorrelief', **params)
    return GDALMetaTileProcessor(processor)


def create_gdal_rastertopng_processor(**params):
    processor = GDALProcessorFactory('rastertopng', **params)
    return GDALMetaTileProcessor(processor)


def create_gdal_setmetadata_processor(**params):
    processor = GDALProcessorFactory('setmetadata', **params)
    return GDALMetaTileProcessor(processor)


def create_gdal_warp_processor(**params):
    processor = GDALProcessorFactory('warp', **params)
    return GDALMetaTileProcessor(processor)


class _MetaTileProcessorFactory(_Factory):

    GDAL_HILLSHADING = 'gdal_hillshading'
    GDAL_COLORRELIEF = 'gdal_colorrelief'
    GDAL_RASTERTOPNG = 'gdal_rastertopng'
    GDAL_FIXMETADATA = 'gdal_fixmetadata'
    GDAL_WARP = 'gdal_warp'

    PROCESSOR_REGISTRY = {
                    GDAL_HILLSHADING: create_gdal_hillshading_processor,
                    GDAL_COLORRELIEF: create_gdal_colorrelief_processor,
                    GDAL_RASTERTOPNG: create_gdal_rastertopng_processor,
                    GDAL_FIXMETADATA: create_gdal_setmetadata_processor,
                    GDAL_WARP: create_gdal_warp_processor,
                    }

    def __call__(self, prototype, **params):
        creator = self.PROCESSOR_REGISTRY.get(prototype, None)
        if not creator:
            raise RuntimeError('Unsupported type %s' % prototype)
        return creator(**params)


#==============================================================================
# Composer Factory
#==============================================================================
def create_imagemagick_composer(**params):
    composer = None
    return ImageMagicMetaTileComposer(composer)


class _MetaTileComposerFactory(_Factory):

    IM = 'imagemagick'

    COMPOSER_REGISTRY = {IM: create_imagemagick_composer, }

    def __call__(self, prototype, **params):
        creator = self.COMPOSER_REGISTRY.get(prototype, None)
        if not creator:
            raise RuntimeError('Unsupported type %s' % prototype)
        return creator(**params)


#==============================================================================
# Renderer Factory
#==============================================================================
def create_datasource_renderer(**params):
    assert 'datasource' in params
    datasource = params['datasource']
    return DataSourceMetaTileRenderer(datasource)


def create_processing_renderer(**params):
    assert 'processor' in params
    assert 'source_renderer' in params
    processor = params['processor']
    source_renderer = params['source_renderer']
    return ProcessingMetaTileRenderer(processor, source_renderer)


def create_composite_renderer(**params):
    assert 'composer' in params
    assert 'source_renderers' in params
    composer = params['composer']
    source_renderers = params['source_renderers']
    return CompositeMetaTileRenderer(composer, *source_renderers)


class _MetaTileRendererFactory(_Factory):

    DATASOURCE_RENDERER = 'datasource_renderer'
    PROCESSING_RENDERER = 'processing_renderer'
    COMPOSITE_RENDERER = 'composite_renderer'

    COMPOSER_REGISTRY = {DATASOURCE_RENDERER: create_datasource_renderer,
                         PROCESSING_RENDERER: create_processing_renderer,
                         COMPOSITE_RENDERER: create_composite_renderer,
                         }

    def __call__(self, prototype, **params):
        creator = self.COMPOSER_REGISTRY.get(prototype, None)
        if not creator:
            raise RuntimeError('Unsupported type %s' % prototype)
        return creator(**params)


MetaTileDataSourceFactory = _MetaTileDataSourceFactory()
MetaTileProcessorFactory = _MetaTileProcessorFactory()
MetaTileComposerFactory = _MetaTileComposerFactory()
MetaTileRendererFactory = _MetaTileRendererFactory()
