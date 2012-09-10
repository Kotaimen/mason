# -*- coding:utf-8 -*-
'''
MetaTile renderer factory

Created on Sep 10, 2012
@author: ray
'''
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

    def __init__(self, registry=dict()):
        self._registry = registry

    def __call__(self, klass_type, **params):
        klass = self._registry.get(klass_type, None)
        if not klass:
            raise RuntimeError('Unsupported type %s' % klass_type)

        return klass(**params)


#==============================================================================
# DataSource Factory
#==============================================================================
DATASOURCE_REGISTRY = dict(cartographer=CartographerMetaTileDataSource)
MetaTileDataSourceFactory = _Factory(DATASOURCE_REGISTRY)

#==============================================================================
# Processor Factory
#==============================================================================
PROCESSOR_REGISTRY = dict(gdal=GDALMetaTileProcessor)
MetaTileProcessorFactory = _Factory(PROCESSOR_REGISTRY)

#==============================================================================
# Composer Factory
#==============================================================================
COMPOSER_REGISTRY = dict(imagemagic=ImageMagicMetaTileComposer)
MetaTileComposerFactory = _Factory(COMPOSER_REGISTRY)

#==============================================================================
# Renderer Factory
#==============================================================================
RENDERER_REGISTRY = dict(datasource=DataSourceMetaTileRenderer,
                         processing=ProcessingMetaTileRenderer,
                         composite=CompositeMetaTileRenderer,)
RendererFactory = _Factory(RENDERER_REGISTRY)
