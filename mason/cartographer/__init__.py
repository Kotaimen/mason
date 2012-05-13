import warnings
from .errors import *


CLASS_REGISTRY = dict()

try:
    from .mapniker import MapnikRaster
except ImportError:
    warnings.warn('Can not import mapnik, mapnikmaker is not available')
    CLASS_REGISTRY['mapnik'] = None
else:
    CLASS_REGISTRY['mapnik'] = MapnikRaster

try:
    from .gdaldem import GDALHillShade, GDALColorRelief, GDALDEMRaster
except ImportError:
    warnings.warn('Can not import gdal or sqlalchemy, gdalmaker not available')
    CLASS_REGISTRY['gdal_hillshade'] = None
    CLASS_REGISTRY['gdal_colorrelief'] = None
else:
    CLASS_REGISTRY['gdal_hillshade'] = GDALHillShade
    CLASS_REGISTRY['gdal_colorrelief'] = GDALColorRelief


def create_cartographer(prototype, **params):
    try:
        klass = CLASS_REGISTRY[prototype]
    except KeyError:
        raise Exception('Unkown prototype %s' % prototype)

    if klass is None:
        raise Exception('%s is not available.' % prototype)

    return klass(**params)
