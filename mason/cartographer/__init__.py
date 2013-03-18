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
