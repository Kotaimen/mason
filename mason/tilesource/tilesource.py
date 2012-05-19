'''
Created on May 10, 2012

@author: ray
'''
import time
import mimetypes
from ..utils import Timer
from ..tilelib import Tile, MetaTile


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

    def close(self):
        raise NotImplementedError


#==============================================================================
# Cartographer Tile Source
#==============================================================================
class CartographerTileSource(TileSource):

    """ Tile Source of Cartographer """

    def __init__(self, tag, cartographer):
        TileSource.__init__(self, tag)
        self._cartographer = cartographer

        # Make a metadata template
        ext = self._cartographer.data_type
        if ext.startswith('png'):
            ext = 'png'
        elif ext.lower().endswith('tiff'):
            ext = 'tif'
        elif ext.lower() == 'jpeg':
            ext = 'jpg'
        mimetype = mimetypes.guess_type('ext.%s' % ext)[0]
        self._metadata = dict(ext=ext,
                              mimetype=mimetype)

    def get_tile(self, tile_index):
        """ Generate specified tile """

        # Tile is always square
        width = height = tile_index.pixel_size
        size = (width, height)
        # Render area in crs coordinate
        envelope = tile_index.envelope.make_tuple()

        # Call cartographer to do rendering
        data = self._cartographer.doodle(envelope, size)

        # Generate some metadata
        metadata = dict(self._metadata)
        metadata['mtime'] = time.time()

        # Create a new Tile and return it
        tile = Tile.from_tile_index(tile_index, data, metadata)
        return tile

    def get_metatile(self, metatile_index):
        """ Generate specified metatile """
        # XXX: This is almost same as get_tile...

        width = height = metatile_index.pixel_size
        size = (width, height)

        envelope = metatile_index.envelope.make_tuple()

        data = self._cartographer.doodle(envelope, size)

        metadata = dict(self._metadata)
        metadata['mtime'] = time.time()

        # Create a new Tile and return it
        metatile = MetaTile.from_tile_index(metatile_index, data, metadata)
        return metatile
