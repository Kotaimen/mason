'''
Created on May 21, 2012

@author: ray
'''
import time

from ..core import Tile, MetaTile
from ..utils import boxcrop
from .tilesource import TileSource


#==============================================================================
# Composer Tile Source
#==============================================================================
class ComposerTileSource(TileSource):

    """ Composer Tile Source

    tag
        composer tag

    sources
        list of instances of tile source

    storages
        list of instances of tile storage

    composer
        composer instance

    """

    def __init__(self, tag, sources, composer, buffer_size=0):
        TileSource.__init__(self, tag)
        self._sources = sources
        self._composer = composer
        self._buffer_size = buffer_size

    def get_tile(self, tile_index):
        """ Gets tile """

        buffer_size = self._buffer_size

        tile_layer_list = list()
        for source in self._sources:
            # get tile from storage
            layer = source.get_tile(tile_index, buffer_size)

            if layer is None:
                raise Exception('Tile Source is Missing!')

            tile_layer_list.append(layer)

        renderdata = self._composer.compose(tile_layer_list)

        data = renderdata.data
        data_type = renderdata.data_type

        ext = data_type.ext
        mimetype = data_type.mimetype
        mtime = time.time()

        if buffer_size > 0:
            side = tile_index.pixel_size
            size = (side, side)

            left = top = buffer_size
            right = bottom = buffer_size + side

            cropbox = (left, top, right, bottom)
            data = boxcrop(data, ext, size, cropbox)

        metadata = dict(ext=ext, mimetype=mimetype, mtime=mtime)

        tile = Tile.from_tile_index(tile_index, data, metadata)
        return tile

    def get_metatile(self, metatile_index):

        tile_list = list()
        for tile_index in metatile_index.fission():

            tile = self.get_tile(tile_index)

            tile_list.append(tile)

        ext = tile_list[0].metadata['ext']
        mimetype = tile_list[0].metadata['mimetype']
        mtime = time.time()

        metadata = dict(ext=ext, mimetype=mimetype, mtime=mtime)
        metatile = MetaTile(metatile_index, tile_list, metadata)

        return metatile

    def close(self):
        pass
