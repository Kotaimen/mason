'''
Created on May 10, 2012

@author: ray
'''


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
        mtime    production date
        ext      data type

    """
    def __init__(self, tag):
        self._tag = tag
        self._metadata = dict()

    @property
    def tag(self):
        return self._tag

    def get_tile(self, tile_index):
        raise NotImplementedError

    def get_metatile(self, metatile_index):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError
