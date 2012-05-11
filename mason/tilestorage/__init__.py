import warnings

# Create a dictionary containing name->class map, those
#  can't be imported will be ignored

# ===== Special ================================================================

from .tilestorage import TileStorage, NullTileStorage

from .special import DefaultTileStorage

from .special import CascadeTileStorage as _CascadeTileStorageImp

# ===== Storage Backend ========================================================

from .filesystem import FileSystemTileStorage

try:
    from .memcached import MemCachedTileStorage
except ImportError as e:
    warnings.warn("Can't import memcache, MemCachedTileStorage is not available")
    MemCachedTileStorage = None

try:
    from .mbtiles import MBTilesTileStorage
except ImportError as e:
    warnings.warn("Can't import mbtiles, MBTilesTileStorage is not available")
    MBTilesTileStorage = None


# ===== Storage Factory ========================================================

def CascadeTileStorage(tag, storages, read_mode='cache', write_mode='last'):

    # HACK: CascadeTileStorage only accepts storage object as parameter, but
    #       for convince we really want to write storage parameters in the
    #       configuration, and write nested cascade storages, thus replace
    #       the original constructor here:

    factory = TileStorageFactory()
    storage_objects = list()

    for storage_param in storages:
        storage_param = dict(storage_param)
        tag = storage_param['tag']
        prototype = storage_param['prototype']
        del storage_param['tag']
        del storage_param['prototype']

        storage_objects.append(factory(prototype, tag, **storage_param))

    return _CascadeTileStorageImp(tag, storage_objects,
                                  read_mode=read_mode,
                                  write_mode=write_mode)

CascadeTileStorage.__doc__ = _CascadeTileStorageImp.__doc__


class TileStorageFactory(object):

    """ Tile storage factory class """

    CLASS_REGISTRY = dict(null=NullTileStorage,
                          default=DefaultTileStorage,
                          cascade=CascadeTileStorage,
                          filesystem=FileSystemTileStorage,
                          memcache=MemCachedTileStorage,
                          mbtiles=MBTilesTileStorage,
                          )

    def __call__(self, prototype, tag, **params):
        try:
            class_prototype = self.CLASS_REGISTRY[prototype]
        except KeyError:
            raise Exception('Unknown tile storage prototype "%s"' % prototype)

        if class_prototype is None:
            raise Exception('Tile storage prototype "%s" is not available, '\
                            'probably missing support driver?' % prototype)

        return class_prototype(tag, **params)


def create_tilestorage(prototype, tag, **params):

    """ Create a tile storage """

    # TODO: Add usage comments

    return TileStorageFactory()(prototype, tag, **params)
