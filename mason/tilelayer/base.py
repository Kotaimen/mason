'''
Created on Jun 12, 2012

@author: ray
'''


class TileLayer(object):

    def __init__(self, tag):
        self._tag = tag

    @property
    def tag(self):
        return self._tag

    def get_tile(self, tile_index, buffer_size):
        raise NotImplementedError

    def get_metatile(self, metatile_index, buffer_size):

        for tile_index in metatile_index.fission():
            layer = self.get_tile(tile_index, buffer_size)
            yield layer


class TileLayerData(object):

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
