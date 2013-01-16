import warnings
import os
try:
    import simplejson as json
except ImportError:
    import json

# Create a dictionary containing name->class map, those
#  can't be imported will be ignored

# ===== Special ================================================================

from .tilestorage import TileStorage, NullTileStorage

# ===== Storage Backend ========================================================

from .filesystem import FileSystemTileStorage
from .metatilecache import MetaTileCache
from .cluster import ClusterTileStorage

try:
    from .memcached import MemcachedTileStorage
except ImportError:
    MemcachedTileStorage = None

from .mbtiles import MBTilesTileStorage, MBTilesTileStorageWithBackgroundWriter

from .cascade import CascadeTileStorage as CascadeTileStorage

# ===== Storage Factory ========================================================


def CascadeTileStorageWrapper(pyramid, metadata,
                              violate=None, presistent=None, write_back=False):

    # HACK: CascadeTileStorage only accepts storage object as parameter, but
    #       for convince we really want to write storage parameters in the
    #       configuration, and write nested cascade storages, thus inject and
    #       replace the original constructor here:

    violate_storage = create_tilestorage(violate[0], pyramid,
                                         metadata, **violate[1])
    presistent_storage = create_tilestorage(presistent[0], pyramid,
                                            metadata, **presistent[1])

    return CascadeTileStorage(pyramid, metadata,
                              violate=violate_storage,
                              presistent=presistent_storage,
                              write_back=write_back)


# ===== Storage Factory ========================================================

class TileStorageFactory(object):

    """ Tile storage factory class """

    CLASS_REGISTRY = dict(null=NullTileStorage,
                          filesystem=FileSystemTileStorage,
                          metacache=MetaTileCache,
                          memcache=MemcachedTileStorage,
                          mbtiles=MBTilesTileStorage,
                          mbtilesbw=MBTilesTileStorageWithBackgroundWriter,
                          cluster=ClusterTileStorage,
                          cascade=CascadeTileStorageWrapper,
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


MAGIC = {FileSystemTileStorage.CONFIG_VERSION.split('-', 1)[0]: FileSystemTileStorage,
         MetaTileCache.CONFIG_VERSION.split('-', 1)[0]: MetaTileCache,
         ClusterTileStorage.CONFIG_VERSION.split('-', 1)[0]: FileSystemTileStorage,
         }


def attach_tilestorage(prototype, **args):
    if prototype == 'filesystem':
        root = args['root']
        assert os.path.isdir(root)
        config_filename = os.path.join(root, FileSystemTileStorage.CONFIG_FILENAME)
        if not os.path.exists(config_filename):
            RuntimeError('Given directory is not a FileSystemTileStorage')
        magic = json.load(config_filename)['magic'].split('-', 1)[0]
        return MAGIC[magic].from_config(root)
    elif prototype == 'mbtiles':
        database = args['database']
        return MBTilesTileStorage.from_mbtiles(database)
    raise RuntimeError("Dont know how to attach to %s:%s" % (prototype, args))
