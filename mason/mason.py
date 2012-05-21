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

    This is the "facade" class and hides details of tilesource/storage, and is
    supposed be used by server frontend and rendering scripts.

    Usually mason instance is created from configuration file using
    create_mason_from_config().
    """

    def __init__(self):
        self._layers = dict()

    def add_layer(self, layer):
        """ Add a layer to Mason """
        self._layers[layer.tag] = layer

    def delete_layer(self, tag):
        """ Remove existing layer from Mason """
        del self._layers[tag]

    def get_layer(self, alias):
        """ Returns a layer object """
        return self._layers[alias]

    def craft_tile(self, alias, z, x, y):
        """ Craft a tile from tilesource or retrive one from tile storage.

        Returns a tuple of (data, metatdata).  data is a bytes array of tile
        data (usually an image), metadata is a dict of key-value pairs.
        """
        try:
            layer = self._layers[alias]
        except KeyError:
            raise InvalidLayer(alias)

        tile = layer.get_tile(z, x, y)
        if tile is None:
            raise TileNotFound('%s/%d/%d/%d' % (alias, z, x, y))

        return tile.data, tile.metadata

    def get_layers(self):
        """ Get a list of tile aliases """
        return self._layers.keys()

    def get_layer_metadata(self, alias):
        """ Get layer metadata, return empty dict if the layer does not exist """
        try:
            return self._layers[alias].metadata
        except KeyError:
            return {}

    def close(self):
        for layer in self._layers.itervalues():
            layer.close()

