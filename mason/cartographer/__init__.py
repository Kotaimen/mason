import warnings
from .errors import *


#==============================================================================
# Cartographer Prototype
#==============================================================================
try:
    from .mapniker import MapnikRaster
except ImportError:
    warnings.warn('Can not import mapnik, mapnikmaker is not available')
    MapnikRaster = None

try:
    from .gdaldem import GDALHillShade, GDALColorRelief, GDALDEMRaster
except ImportError:
    warnings.warn('Can not import gdal or sqlalchemy, gdalmaker not available')
    GDALHillShade = None
    GDALColorRelief = None
    GDALDEMRaster = None


#==============================================================================
# Cartographer Factory
#==============================================================================
class CartographerFactory(object):

    CLASS_REGISTRY = dict(mapnik=MapnikRaster,
                          hillshade=GDALHillShade,
                          colorrelief=GDALColorRelief,)

    def __call__(self, prototype, **params):
        class_prototype = self.CLASS_REGISTRY.get(prototype, None)
        if class_prototype is None:
            raise Exception('Unknown cartographer prototype "%s"' % prototype)

        return class_prototype(**params)


def create_cartographer(prototype, **params):
    """ Create a cartographer """
    return CartographerFactory()(prototype, **params)
