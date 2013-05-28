# -*- coding:utf-8 -*-

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
    from .rasterdataset import RasterDataset
except ImportError:
    RasterDataset = None

try:
    from .shaderelief import ShadeRelief
except ImportError:
    raise
    ShadeRelief = None

#==============================================================================
# Cartographer Factory
#==============================================================================
class _CartographerFactory(object):

    CLASS_REGISTRY = dict(mapnik=Mapnik,
                          postgis=PostGIS,
                          shaderelief=ShadeRelief,
                          dataset=RasterDataset,)

    def __call__(self, prototype, **params):
        creator = self.CLASS_REGISTRY.get(prototype, None)
        if creator is None:
            raise Exception('Cartographer "%s" is not available, missing support libraries?' % prototype)

        return creator(**params)

CartographerFactory = _CartographerFactory()
