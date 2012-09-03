import warnings

# Create a dictionary containing name->class map, those
#  can't be imported will be ignored

# ===== Special ================================================================

from .tilestorage import TileStorage, NullTileStorage

# ===== Storage Backend ========================================================

from .filesystem import FileSystemTileStorage

# ===== Storage Factory ========================================================


class TileStorageFactory(object):

    """ Tile storage factory class """

    CLASS_REGISTRY = dict(null=NullTileStorage,
                          filesystem=FileSystemTileStorage,
                          )

    def __call__(self, prototype, pyramid, metadata, **params):
        try:
            class_prototype = self.CLASS_REGISTRY[prototype]
        except KeyError:
            raise Exception('Unknown tile storage prototype "%s"' % prototype)

        if class_prototype is None:
            raise Exception('Tile storage prototype "%s" is not available, '\
                            'probably missing support driver?' % prototype)

        return class_prototype(pyramid, metadata, **params)


def create_tilestorage(prototype, tag, **params):

    """ Create a tile storage """

    # TODO: Add usage comments

    return TileStorageFactory()(prototype, tag, **params)
