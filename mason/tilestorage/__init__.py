
import warnings

from .tilestorage import TileStorage, NullTileStorage

CLASS_REGISTRY = dict(null=NullTileStorage,

                      )

def create_tilestorage(prototype, tag, params):
    klass = CLASS_REGISTRY[prototype]
    return klass(tag, **params)

