import warnings
from .errors import *
from .datatype import create_data_type

#==============================================================================
# Cartographer Prototype
#==============================================================================
try:
    from .mapniker import MapnikRaster
except ImportError:
    warnings.warn('Can not import mapnik, mapnikmaker is not available')
    MapnikRaster = None

try:
    from .gdaldem import GDALHillShade, GDALColorRelief
except ImportError:
    warnings.warn('Can not import gdal or sqlalchemy, gdalmaker not available')
    GDALHillShade = None
    GDALColorRelief = None


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
            raise Exception('Unknown cartographer type "%s"' % prototype)

        # custom values
        if 'data_type' in params:
            datatype_name = params['data_type']
            del params['data_type']

            data_parameters = None
            if 'data_parameters' in params:
                data_parameters = params['data_parameters']
                del params['data_parameters']

            data_type = create_data_type(datatype_name, data_parameters)
        else:
            data_type = create_data_type('png', None)

        params['data_type'] = data_type

        return class_prototype(**params)


def create_cartographer(prototype, **params):
    """ Create a cartographer """
    return CartographerFactory()(prototype, **params)
