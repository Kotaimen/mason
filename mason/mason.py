'''
Created on May 14, 2012

@author: Kotaimen
'''


class InvalidLayer(Exception):
    pass


class TileNotFound(Exception):
    pass


class Mason(object):

    """ The "TileLayerManager", create and manage one or more Tile layers


    """

    def __init__(self, mode='default'):
        assert mode in ['default', 'readonly', 'rewrite']
        self._mode = mode
        self._layers = dict()

    def add_layer(self, layer):
        self._layers[layer.tag] = layer

    def delete_layer(self, tag):
        del self._layers[tag]

    def craft_tile(self, alias, z, x, y):
        try:
            layer = self._layers[alias]
        except KeyError:
            raise InvalidLayer(alias)

        tile = layer.get_tile(z, x, y)
        if tile is None:
            raise TileNotFound('%s/%d/%d/%d' % (alias, z, x, y))

        return tile.data, tile.metadata

    def craft_metatile(self):
        raise NotImplementedError

    def get_layers(self):
        return self._layers.keys()

    def get_layer_metadata(self, alias):
        try:
            return self._layers[alias].metadata
        except KeyError:
            return {}

    def close(self):
        for layer in self._layers.itervalues():
            layer.close()






