'''
Created on Jun 12, 2012

@author: ray
'''


class TileLayer(object):

    """ Tile Layer Base Class """

    def __init__(self, tag):
        self._tag = tag

    @property
    def tag(self):
        return self._tag

    def get_layer(self, tile_index, buffer_size):
        """ Gets tile layer from tile index

        returns TileLayerData if available, otherwise, returns None.
        """
        raise NotImplementedError


class TileLayerData(object):

    """ Tile Layer Data """

    def __init__(self, data, data_type, size):
        self._data = data
        self._size = size
        self._data_type = data_type

    @property
    def data(self):
        return self._data

    @property
    def size(self):
        return self._size

    @property
    def data_type(self):
        return self._data_type
