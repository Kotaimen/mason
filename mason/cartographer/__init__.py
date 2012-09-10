from .gdalraster import GDALRaster
from .gdaltools import create_gdal_processor

#==============================================================================
# Cartographer Prototype
#==============================================================================
try:
    from .mapniker import Mapnik
except ImportError:
    Mapnik = None

#==============================================================================
# Cartographer Factory
#==============================================================================

class CartographerFactory(object):

    CLASS_REGISTRY = dict(mapnik=Mapnik,

                          )

    def __call__(self, prototype, **params):
        klass = self.CLASS_REGISTRY.get(prototype, None)
        if klass is None:
            raise Exception('Unknown cartographer type "%s"' % prototype)

        return klass(**params)


def create_cartographer(prototype, **params):
    """ Create a cartographer """
    return CartographerFactory()(prototype, **params)
