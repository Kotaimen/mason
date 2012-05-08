import warnings

# Create a dictionary containing name->class map, those
#  can't be imported will be ignored

from .tilestorage import TileStorage, NullTileStorage
CLASS_REGISTRY = dict(null=NullTileStorage)

from .filesystem import FileSystemTileStorage
CLASS_REGISTRY['filesystem'] = FileSystemTileStorage

try:
    from .memcached import MemCachedTileStorage
except ImportError as e:
    warnings.warn("Can't import memcache, MemCachedTileStorage is not available")
    CLASS_REGISTRY['memcache'] = None
else:
    CLASS_REGISTRY['memcache'] = MemCachedTileStorage

try:
    from .mbtiles import MBTilesTileStorage
except ImportError as e:
    warnings.warn("Can't import mbtiles, MBTilesTileStorage is not available")
    CLASS_REGISTRY['mbtiles'] = None
else:
    CLASS_REGISTRY['mbtiles'] = MBTilesTileStorage


def create_tilestorage(prototype, tag, **params):
    try:
        klass = CLASS_REGISTRY[prototype]
    except KeyError:
        raise Exception('Unknown tile storage prototype "%s"' % prototype)

    if klass is None:
        raise Exception('Tile storage prototype "%s" is not available, '\
                        'probably missing support driver?' % prototype)

    return klass(tag, **params)
