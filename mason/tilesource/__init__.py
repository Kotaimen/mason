
from ..cartographer import create_cartographer
from ..tilestorage import create_tilestorage
from ..composer import create_tile_composer

from .singleton import CartographerTileSource
from .composer import ComposerTileSource
from .null import NullTileSource

null_tile_source = NullTileSource()


#==============================================================================
# Creator Class
#==============================================================================
class TileSourceCreator(object):

    def __call__(self, tag, **params):
        raise NotImplementedError


class MapnikTileSourceCreator(TileSourceCreator):

    """ Cartographer Tile Source Creator """

    def __call__(self, tag, **params):
        cartographer = create_cartographer('mapnik', **params)
        return CartographerTileSource(tag, cartographer)


class HillShadeTileSourceCreator(TileSourceCreator):

    """ Cartographer Tile Source Creator """

    def __call__(self, tag, **params):
        cartographer = create_cartographer('hillshade', **params)
        return CartographerTileSource(tag, cartographer)


class ColorReliefTileSourceCreator(TileSourceCreator):

    """ Cartographer Tile Source Creator """

    def __call__(self, tag, **params):
        cartographer = create_cartographer('colorrelief', **params)
        return CartographerTileSource(tag, cartographer)


class ComposerCreator(TileSourceCreator):

    """ Composer Tile Source Creator """

    def __call__(self, tag, **params):

        sources = params['sources']
        storages = params['storages']

        data_type = params['image_type']

        # create sources
        source_list = list()
        for n, source_cfg in enumerate(sources):
            if source_cfg is None:
                source_cfg = {'prototype': 'null'}
            if 'tag' not in source_cfg:
                source_cfg['tag'] = '%s_%s' % (tag, n)
            source = create_tile_source(**source_cfg)
            source_list.append(source)

        # create storages
        storage_list = list()
        for n, storage_cfg in enumerate(storages):
            if storage_cfg is None:
                storage_cfg = {'prototype': 'null'}
            if 'tag' not in storage_cfg:
                storage_cfg['tag'] = '%s_%s' % (tag, n)
            storage = create_tilestorage(**storage_cfg)
            storage_list.append(storage)

        del params['sources']
        del params['storages']
        del params['image_type']

        # create composer
        composer = create_tile_composer('imagemagick', tag, data_type,
                                        **params)

        return ComposerTileSource(tag, source_list, storage_list, composer)


class NullTileSourceCreator(TileSourceCreator):

    def __call__(self, tag, **params):
        return null_tile_source


#==============================================================================
# Tile Source Factory
#==============================================================================
class TileSourceFactory(object):

    """ Tile Source Factory """

    CLASS_REGISTRY = dict(mapnik=MapnikTileSourceCreator(),
                          hillshade=HillShadeTileSourceCreator(),
                          colorrelief=ColorReliefTileSourceCreator(),
                          composer=ComposerCreator(),
                          null=NullTileSourceCreator(),
                          )

    def __call__(self, prototype, tag, **params):

        class_prototype = self.CLASS_REGISTRY.get(prototype, None)
        if class_prototype is None:
            raise Exception('Unknown tile source prototype "%s"' % prototype)

        return class_prototype(tag, **params)


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
