
from ..cartographer import create_cartographer
from ..tilestorage import create_tilestorage
from ..composer import create_tile_composer

from .singleton import CartographerTileSource
from .composer import ComposerTileSource


#==============================================================================
# Creator Class
#==============================================================================
class TileSourceCreator(object):

    def __call__(self, tag, **params):
        raise NotImplementedError


class CartographerCreator(TileSourceCreator):

    """ Cartographer Tile Source Creator """

    def __call__(self, prototype, tag, **params):
        cartographer = create_cartographer(prototype, **params)
        return CartographerTileSource(tag, cartographer)


class ComposerCreator(TileSourceCreator):

    """ Composer Tile Source Creator """

    def __call__(self, prototype, tag, sources, storages, **params):

        # create sources
        source_list = list()
        for n, source_cfg in enumerate(sources):
            if 'tag' not in source_cfg:
                source_cfg['tag'] = '%s_%s' % (tag, n)
            source = create_tile_source(**source_cfg)
            source_list.append(source)

        # create storages
        storage_list = list()
        for n, storage_cfg in enumerate(storages):
            if 'tag' not in storage_cfg:
                storage_cfg['tag'] = '%s_%s' % (tag, n)
            storage = create_tilestorage(**storage_cfg)
            storage_list.append(storage)

        # create composer
        composer = create_tile_composer('imagemagick', tag, **params)

        return ComposerTileSource(tag, source_list, storage_list, composer)


#==============================================================================
# Tile Source Factory
#==============================================================================
class TileSourceFactory(object):

    """ Tile Source Factory """

    CLASS_REGISTRY = dict(mapnik=CartographerCreator(),
                          hillshade=CartographerCreator(),
                          colorrelief=CartographerCreator(),
                          composer=ComposerCreator(),
                          )

    def __call__(self, prototype, tag, **params):

        class_prototype = self.CLASS_REGISTRY.get(prototype, None)
        if class_prototype is None:
            raise Exception('Unknown tile source prototype "%s"' % prototype)

        return class_prototype(prototype, tag, **params)


def create_tile_source(prototype, tag, **params):
    """ Create a Tile Source

    prototype
        tile source prototype

    tag
        a tile source tag for distinguishing different tile source

    params
        parameters of tile source

    configuration example
        'source':
            {
            'prototype': 'mapnik',
            'tag': 'example',
            'theme_root': './samples/themes/',
            'theme_name': 'worldaltas',
            'image_type': 'png',
            },
    """
    return TileSourceFactory()(prototype, tag, **params)
