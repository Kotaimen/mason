'''
Created on May 10, 2012

@author: ray
'''
import time
from ..utils import Timer
from ..tilelib import Tile


#==============================================================================
# Errors
#==============================================================================
class TileSourceError(Exception):
    pass


#==============================================================================
# Tile Source
#==============================================================================
class TileSource(object):

    """ Tile Source Base Class

    Tile Source is a tile-based map data resource that receives a tile/metatile
    index to create a tile/metatile.

    get_tile
        get a tile with specified tile index

    get_metatile
        get a meta-tile with meta-tile index

    tile/metatile metadata:
        timestamp
            production date
        ext
            data type

    """
    def __init__(self, tag):
        self._tag = tag

    def get_tile(self, tile_index):
        raise NotImplementedError

    def get_metatile(self, metatile_index):
        raise NotImplementedError


#==============================================================================
# Cartographer Tile Source
#==============================================================================
class CartographerTileSource(TileSource):

    """ Tile Source of Cartographer """

    def __init__(self, tag, cartographer):
        TileSource.__init__(self, tag)
        self._cartographer = cartographer

    def get_tile(self, tile_index):
        """ Get tile according to the tile index """
        # tile is a square.
        width = height = tile_index.pixel_size

        size = (width, height)
        envelope = tile_index.envelope.make_tuple()

        with Timer('Tile doodle time taken: %(time)s'):
            data = self._cartographer.doodle(envelope, size)

        metadata = dict()
        metadata['timestamp'] = time.time()
        tile = Tile.from_tile_index(tile_index, data, metadata)

        return tile

    def get_metatile(self, metatile_index):
        """ TBD """
        raise NotImplementedError
