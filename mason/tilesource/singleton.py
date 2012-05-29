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

    """ Tile Source of Cartographer """

    def __init__(self, tag, cartographer):
        TileSource.__init__(self, tag)
        self._cartographer = cartographer

    def get_tile(self, tile_index):
        """ Generate specified tile """

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
        tile = Tile.from_tile_index(tile_index, renderdata.data, metadata)
        return tile

    def get_metatile(self, metatile_index):
        """ Generate specified metatile """
        # XXX: This is almost same as get_tile...

        width = height = metatile_index.pixel_size
        size = (width, height)

        envelope = metatile_index.envelope.make_tuple()

        renderdata = self._cartographer.doodle(envelope, size)

        ext = renderdata.data_type.ext
        mimetype = renderdata.data_type.mimetype
        metadata = dict(ext=ext, mimetype=mimetype, mtime=time.time())

        # Create a new Tile and return it
        metatile = MetaTile.from_tile_index(metatile_index,
                                            renderdata.data,
                                            metadata)
        return metatile
