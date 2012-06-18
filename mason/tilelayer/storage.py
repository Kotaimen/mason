'''
Created on Jun 12, 2012

@author: ray
'''
from ..core import create_data_type
from .base import TileLayer, TileLayerData

import subprocess


class StorageLayer(TileLayer):

    def __init__(self, tag, storage,
                 border_color='transparent'):
        TileLayer.__init__(self, tag)
        self._storage = storage
        self._border_color = border_color

    def _process_tile_data(self, tile):
        return tile.data

    def get_layer(self, tile_index, buffer_size):

        side = tile_index.pixel_size + buffer_size * 2
        size = (side, side)

        tile = self._storage.get(tile_index)
        if tile is None:
            return None

        data = self._process_tile_data(tile)

        ext = tile.metadata['ext']

        if buffer_size > 0:
            # XXX: Need find a way to expand border pixels otherwise 
            #      sharpen will have artifacts around original border
            args = ['convert',
                   '%s:-' % ext,
                   '-bordercolor', self._border_color,
                   '-border',
                   '%dx%d' % (buffer_size, buffer_size),
                   '%s:-' % ext,
                   ]

            popen = subprocess.Popen(args=args,
                                     stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE)
            stdout, stderr = popen.communicate(data)
            retcode = popen.poll()
            if retcode:
                raise subprocess.CalledProcessError(retcode, args)

            data = stdout

        data_type_name = ext
        data_type = create_data_type(data_type_name)
        layer = TileLayerData(data, data_type, size)

        return layer
