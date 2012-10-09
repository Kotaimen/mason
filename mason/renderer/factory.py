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
from .renderer import (DataSourceMetaTileRenderer,
                       ProcessingMetaTileRenderer,
                       CompositeMetaTileRenderer,
                       )


#==============================================================================
# Renderer Factories
#==============================================================================
class _DataSourceRendererFactory(object):

    """ DataSource Renderer Factory

    Create a datasource renderer with a given prototype.
    Mapnik, PostGIS, and Storage is supported now.
    """

    DATASOURCE_REGISTRY = ['mapnik', 'postgis', 'storage']

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

        return DataSourceMetaTileRenderer(metatile_datasource)


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

        return ProcessingMetaTileRenderer(metatile_processor, source)


class _CompositeRendererFactory(object):

    """ Composite Renderer Factory

    Create a composite renderer by given prototype and parameters.
    Imagemagick composer is supported now.
    """

    COMPOSITE_REGISTRY = ['imagemagick', ]

    def __call__(self, prototype, source_list, **params):
        params = dict(params)
        if prototype in self.COMPOSITE_REGISTRY:
            # params: format, command
            composer = ImageMagickComposer(**params)
            metatile_composer = ImageMagicMetaTileComposer(composer)

        else:
            raise RuntimeError('Unknown prototype %s' % prototype)

        return CompositeMetaTileRenderer(metatile_composer, source_list)


DataSourceRendererFactory = _DataSourceRendererFactory()
ProcessingRendererFactory = _ProcessingRendererFactory()
CompositeRendererFactory = _CompositeRendererFactory()
