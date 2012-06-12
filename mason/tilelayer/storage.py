'''
Created on Jun 12, 2012

@author: ray
'''
from ..core import create_data_type
from .base import TileLayer, TileLayerData


class StorageLayer(TileLayer):

    def __init__(self, tag, storage):
        TileLayer.__init__(self, tag)
        self._storage = storage

    def _process_tile_data(self, tile):
        return tile.data

    def get_tile(self, tile_index, buffer_size):

        side = tile_index.pixel_size + buffer_size * 2
        size = (side, side)

        tile = self._storage.get(tile_index)
        if tile is None:
            return None

        data = self._process_tile_data(tile)

        if buffer_size > 0:
            # place to canvas center
            raise NotImplementedError

        ext = tile.metadata['ext']
        data_type_name = ext
        data_type = create_data_type(data_type_name)
        layer = TileLayerData(data, data_type, size)

        return layer

