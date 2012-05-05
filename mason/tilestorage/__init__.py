
import warnings

from .tilestorage import TileStorage, NullTileStorage
from .filesystem import FileSystemTileStorage
CLASS_REGISTRY = dict(null=NullTileStorage,
                      filesystem=FileSystemTileStorage,

                      )


def create_tilestorage(prototype, tag, **params):
    try:
        klass = CLASS_REGISTRY[prototype]
    except KeyError:
        raise Exception('Unknown tile storage prototype "%s"' % prototype)
    return klass(tag, **params)

