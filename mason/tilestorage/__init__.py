import warnings
import os

# Create a dictionary containing name->class map, those
#  can't be imported will be ignored

# ===== Special ================================================================

from .tilestorage import TileStorage, NullTileStorage

# ===== Storage Backend ========================================================

from .filesystem import FileSystemTileStorage
from .metatilecache import MetaTileCache

try:
    from .memcached import MemcachedTileStorage

except ImportError:
    MemcachedTileStorage = None

from .mbtiles import MBTilesTileStorage, MBTilesTileStorageWithBackgroundWriter

# ===== Storage Factory ========================================================


class TileStorageFactory(object):

    """ Tile storage factory class """

    CLASS_REGISTRY = dict(null=NullTileStorage,
                          filesystem=FileSystemTileStorage,
                          metacache=MetaTileCache,
                          memcache=MemcachedTileStorage,
                          mbtiles=MBTilesTileStorage,
                          mbtilesbw=MBTilesTileStorageWithBackgroundWriter,
                          )

    def __call__(self, prototype, pyramid=None, metadata=None, **params):
        try:
            class_prototype = self.CLASS_REGISTRY[prototype]
        except KeyError:
            raise Exception('Unknown tile storage prototype "%s"' % prototype)

        if class_prototype is None:
            raise Exception('Tile storage prototype "%s" is not available, '\
                            'probably missing support driver?' % prototype)

        return class_prototype(pyramid, metadata, **params)


def create_tilestorage(prototype, pyramid=None, metadata=None, **args):

    """ Create a tile storage """

    return TileStorageFactory()(prototype, pyramid, metadata, **args)


def attach_tilestorage(**args):
    if 'pathname' in args:
        pathname = args['pathname']
        if os.path.isdir(pathname):
            if not os.path.exists(os.path.join(pathname, FileSystemTileStorage.CONFIG_FILENAME)):
                RuntimeError('Given directory is not a FileSystemTileStorage')
            # Assume file system tile storage
            return FileSystemTileStorage.from_config(pathname)
        elif pathname.endswith('.mbtiles'):
            # Assume mbtiles tile storage
            return MBTilesTileStorage.from_mbtiles(pathname)
        raise RuntimeError('Invalid tile storage "%s"' % pathname)
    else:
        raise RuntimeError("Don't understand tile storage: " % args)
