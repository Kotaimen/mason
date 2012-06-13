from ..cartographer import create_cartographer
from ..tilestorage import create_tilestorage

try:
    from .colorrelief import ColorReliefStorageLayer
except ImportError:
    ColorReliefStorageLayer = None

try:
    from .hillshade import HillShadeStorageLayer
except ImportError:
    HillShadeStorageLayer = None

try:
    from .storage import StorageLayer
except ImportError:
    StorageLayer = None

try:
    from .cartographer import CartographerLayer
except ImportError:
    CartographerLayer = None


def create_colorrelief_storage_layer(tag, **params):
    storage_cfg = params.pop('source', None)
    if storage_cfg is None:
        raise Exception('Storage Layer needs storage configuration.')

    if 'tag' not in storage_cfg:
        storage_cfg['tag'] = tag

    storage = create_tilestorage(**storage_cfg)

    return ColorReliefStorageLayer(tag, storage, **params)


def create_hillshade_storage_layer(tag, **params):
    storage_cfg = params.pop('source', None)
    if storage_cfg is None:
        raise Exception('Storage Layer needs storage configuration.')

    if 'tag' not in storage_cfg:
        storage_cfg['tag'] = tag

    storage = create_tilestorage(**storage_cfg)

    return HillShadeStorageLayer(tag, storage, **params)


def create_storage_layer(tag, **params):
    storage_cfg = params.pop('source', None)
    if storage_cfg is None:
        raise Exception('Storage Layer needs storage configuration.')

    if 'tag' not in storage_cfg:
        storage_cfg['tag'] = tag

    storage = create_tilestorage(**storage_cfg)

    return StorageLayer(tag, storage, **params)


def create_cartographer_layer(tag, **params):
    cartographer_cfg = params.pop('source', None)
    if not cartographer_cfg:
        raise Exception('Missing source configuration.')

    if 'tag' not in cartographer_cfg:
        cartographer_cfg['tag'] = tag

    cartographer = create_cartographer(**cartographer_cfg)
    return CartographerLayer(tag, cartographer, **params)


class TileLayerFactory(object):

    CREATOR_REGISTRY = dict(colorrelief_storage=create_colorrelief_storage_layer,
                            hillshade_storage=create_hillshade_storage_layer,
                            storage=create_storage_layer,
                            cartographer=create_cartographer_layer,
                            )

    def __call__(self, prototype, tag, **params):
        creator = self.CREATOR_REGISTRY.get(prototype, None)
        if creator is None:
            raise Exception('Unknown TileLayer "%s"' % prototype)

        return creator(tag, **params)


def create_tile_layer(prototype, tag, **params):
    return TileLayerFactory()(prototype, tag, **params)
