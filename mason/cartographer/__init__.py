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

    CLASS_REGISTRY = dict(mapniker=MapnikRaster,
                          hillshade=GDALHillShade,
                          colorrelief=GDALColorRelief,)

    def __call__(self, prototype, **params):
        try:
            class_prototype = self.CLASS_REGISTRY[prototype]
        except KeyError:
            raise Exception('Unkown prototype %s' % prototype)

        if class_prototype is None:
            raise Exception('Cartographer prototype %s is not \
                             available.' % prototype)

        return class_prototype(**params)


def create_cartographer(prototype, **params):
    """ Create a cartographer """
    return CartographerFactory()(prototype, **params)
