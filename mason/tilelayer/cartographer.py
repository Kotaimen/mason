'''
Created on Jun 12, 2012

@author: ray
'''
from .base import TileLayer, TileLayerData


class CartographerLayer(TileLayer):

    def __init__(self, tag, cartographer):
        TileLayer.__init__(self, tag)
        self._cartographer = cartographer

    def get_tile(self, tile_index, buffer_size):

        side = tile_index.pixel_size + buffer_size * 2
        size = (side, side)

        envelope = tile_index.buffer_envelope(buffer_size)

        renderdata = self._cartographer.doodle(envelope.make_tuple(), size)

        layer = TileLayerData(renderdata.data,
                              renderdata.data_type,
                              size)

        return layer

