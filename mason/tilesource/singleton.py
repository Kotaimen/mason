'''
Created on May 21, 2012

@author: ray
'''
import time

from ..core import Tile, MetaTile
from .tilesource import TileSource


#==============================================================================
# Cartographer Tile Source
#==============================================================================
class CartographerTileSource(TileSource):

    """ Generate a tile using cartographer """

    def __init__(self, tag, cartographer):
        TileSource.__init__(self, tag)
        self._cartographer = cartographer

    def _get_tile(self, tile_index):

        # Tile is always square
        width = height = tile_index.pixel_size
        size = (width, height)
        # Render area in crs coordinate
        envelope = tile_index.envelope.make_tuple()

        # Call cartographer to do rendering
        renderdata = self._cartographer.doodle(envelope, size)

        # Generate some metadata
        ext = renderdata.data_type.ext
        mimetype = renderdata.data_type.mimetype
        metadata = dict(ext=ext, mimetype=mimetype, mtime=time.time())

        # Create a new Tile and return it
        tile = tile_index.make_tile(renderdata.data, metadata)
        return tile

    def get_tile(self, tile_index):
        """ Generate specified tile """
        return self._get_tile(tile_index)

    def get_metatile(self, metatile_index):
        """ Generate specified tile """
        return self._get_tile(metatile_index)
