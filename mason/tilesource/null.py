'''
Created on May 26, 2012

@author: ray
'''
import time
from ..core.tile import Tile, MetaTile
from .tilesource import TileSource


class NullTileSource(TileSource):

    """ Null Tile Source

    Return a tile with empty data
    """

    def __init__(self):
        TileSource.__init__(self, 'null')

        self._metadata = dict(ext='null')

    def get_tile(self, tile_index):
        metadata = dict(self._metadata)
        metadata['mtime'] = time.time()
        return Tile.from_tile_index(tile_index, '', metadata)

    def get_metatile(self, metatile_index):
        metadata = dict(self._metadata)
        metadata['mtime'] = time.time()
        return MetaTile.from_tile_index(metatile_index, '', metadata)

    def close(self):
        pass
