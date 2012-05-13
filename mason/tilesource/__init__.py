from ..cartographer import create_cartographer
from .tilesource import TileSource, CartographerTileSource


#==============================================================================
# Creator Class
#==============================================================================
class TileSourceCreator(object):

    def __call__(self, tag, **params):
        raise NotImplementedError


class CartographerTileSourceCreator(TileSourceCreator):

    """ Cartographer Tile Source Creator

    params
        cartographer_config
            prototype    cartographer prototype
            params       cartographer parameters
    """

    def __call__(self, tag, **params):

        config = params.get('cartographer_config', None)
        if not config:
            raise Exception('"cartographer_config" is expected.')

        prototype = config['prototype']
        del config['prototype']

        cartographer = create_cartographer(prototype, **config)
        return CartographerTileSource(tag, cartographer)


#==============================================================================
# Tile Source Factory
#==============================================================================
class TileSourceFactory(object):

    """ Tile Source Factory """

    CLASS_REGISTRY = dict(cartographer=CartographerTileSourceCreator())

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

    example
        {
            'prototype':    'cartographer'
            'cartographer_config' : {
                                        'prototype': 'mapnik',
                                        'theme_root': './input/',
                                        'theme_name': 'worldaltas',
                                        'image_type': 'png'
                                    }
       }
    """
    return TileSourceFactory()(prototype, tag, **params)
