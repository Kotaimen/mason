from ..cartographer import create_cartographer
from .tilesource import TileSource, CartographerTileSource


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


#==============================================================================
# Tile Source Factory
#==============================================================================
class TileSourceFactory(object):

    """ Tile Source Factory """

    CLASS_REGISTRY = dict(mapnik=CartographerCreator(),
                          hillshade=CartographerCreator(),
                          colorrelief=CartographerCreator(),
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
