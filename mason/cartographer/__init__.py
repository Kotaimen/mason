
from ..core import create_data_type


#==============================================================================
# Cartographer Prototype
#==============================================================================
try:
    from .mapniker import MapnikRaster
except ImportError:
    MapnikRaster = None

try:
    from .gdaldem import DEMRaster
except ImportError:
    DEMRaster = None


def create_mapnik_cartographer(tag, **params):
    data_type_name = params.pop('data_type', None)
    data_parameters = params.pop('data_parameters', None)

    if data_type_name is None:
        data_type_name = 'gtiff'

    data_type = create_data_type(data_type_name, data_parameters)

    return MapnikRaster(data_type, **params)


def create_raster_cartographer(tag, **params):
    data_type_name = params.pop('data_type', None)
    data_parameters = params.pop('data_parameters', None)

    if data_type_name is None:
        data_type_name = 'png'

    data_type = create_data_type(data_type_name, data_parameters)

    return DEMRaster(data_type, **params)


#==============================================================================
# Cartographer Factory
#==============================================================================
class CartographerFactory(object):

    CLASS_REGISTRY = dict(mapnik=create_mapnik_cartographer,
                          raster=create_raster_cartographer,
                          )

    def __call__(self, prototype, tag, **params):
        creator = self.CLASS_REGISTRY.get(prototype, None)
        if creator is None:
            raise Exception('Unknown cartographer type "%s"' % prototype)

        return creator(tag, **params)


def create_cartographer(prototype, tag, **params):
    """ Create a cartographer """
    return CartographerFactory()(prototype, tag, **params)
