from .gdalraster import GDALRaster
from .gdaltools import (GDALHillShading,
                        GDALColorRelief,
                        GDALRasterToPNG,
                        GDALFixMetaData,
                        GDALWarper,
                        gdal_hillshading,
                        gdal_colorrelief
                        )


#==============================================================================
# Cartographer Prototype
#==============================================================================
try:
    from .mapniker import Mapnik
except ImportError:
    Mapnik = None

try:
    from .postgis import PostGIS
except ImportError:
    PostGIS = None

try:
    from .dataset import RasterDataset
except ImportError:
    RasterDataset = None


#==============================================================================
# Cartographer Factory
#==============================================================================
class _CartographerFactory(object):

    CLASS_REGISTRY = dict(mapnik=Mapnik,
                          postgis=PostGIS,
                          dataset=RasterDataset
                          )

    def __call__(self, prototype, **params):
        creator = self.CLASS_REGISTRY.get(prototype, None)
        if creator is None:
            raise Exception('Unknown cartographer "%s"' % prototype)

        return creator(**params)

CartographerFactory = _CartographerFactory()


#==============================================================================
# GDAL Processor Factory
#==============================================================================
class _GDALProcessorFactory(object):

    CLASS_REGISTRY = dict(hillshading=GDALHillShading,
                          colorrelief=GDALColorRelief,
                          rastertopng=GDALRasterToPNG,
                          fixmetadata=GDALFixMetaData,
                          warp=GDALWarper,
                          )

    def __call__(self, prototype, **params):
        creator = self.CLASS_REGISTRY.get(prototype, None)
        if creator is None:
            raise Exception('Unknown cartographer "%s"' % prototype)

        return creator(**params)

GDALProcessorFactory = _GDALProcessorFactory()
