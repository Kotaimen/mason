
from ..cartographer import create_cartographer
from ..tilestorage import create_tilestorage
from ..composer import create_tile_composer
from ..tilelayer import create_tile_layer

from .carto import CartographerTileSource
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
        cartographer = create_cartographer('mapnik', tag, **params)
        return CartographerTileSource(tag, cartographer)


class RasterTileSourceCreator(TileSourceCreator):

    """ Cartographer Tile Source Creator """

    def __call__(self, tag, **params):
        cartographer = create_cartographer('raster', tag, **params)
        return CartographerTileSource(tag, cartographer)


class ComposerCreator(TileSourceCreator):

    """ Composer Tile Source Creator """

    def __call__(self, tag, **params):

        tile_layer_cfgs = params.pop('tilelayers', None)
        if not tile_layer_cfgs:
            raise Exception('Missing Composite layers.')

        buffer_size = params.pop('buffer_size', 0)

        tile_layer_list = list()
        for layer_cfg in tile_layer_cfgs:
            if 'tag' not in layer_cfg:
                layer_cfg['tag'] = tag
            tile_layer = create_tile_layer(**layer_cfg)
            tile_layer_list.append(tile_layer)

        # create composer
        composer = create_tile_composer('imagemagick', tag, **params)

        return ComposerTileSource(tag, tile_layer_list, composer, buffer_size)


class NullTileSourceCreator(TileSourceCreator):

    def __call__(self, tag, **params):
        return null_tile_source


#==============================================================================
# Tile Source Factory
#==============================================================================
class TileSourceFactory(object):

    """ Tile Source Factory """

    CLASS_REGISTRY = dict(mapnik=MapnikTileSourceCreator(),
                          raster=RasterTileSourceCreator(),
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
