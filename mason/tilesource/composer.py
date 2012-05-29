'''
Created on May 21, 2012

@author: ray
'''
import time

from ..tilelib import Tile, MetaTile
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

    def __init__(self, tag, sources, storages, composer):
        TileSource.__init__(self, tag)
        assert len(sources) == len(storages)
        self._sources = sources
        self._storages = storages
        self._composer = composer

    def get_tile(self, tile_index):
        """ Gets tile """

        tiles = list()
        for source, storage in zip(self._sources, self._storages):
            # get tile from storage
            tile = storage.get(tile_index)

            if tile is None:
                # get tile from source
                tile = source.get_tile(tile_index)
                if tile is None:
                    raise Exception('Tile Source is Missing!')

                storage.put(tile)

            tiles.append(tile)

        renderdata = self._composer.compose(tiles)

        data_type = renderdata.data_type
        metadata = dict(ext=data_type.ext,
                        mimetype=data_type.mimetype,
                        mtime=time.time())

        tile = Tile.from_tile_index(tile_index, renderdata.data, metadata)
        return tile

    def get_metatile(self, metatile_index):
        """ Gets metatile """

        metatiles = list()
        for source in self._sources:
            metatile = source.get_metatile(metatile_index)
            if metatile is None:
                raise Exception('MetaTile Source is Missing!')
            metatiles.append(metatile)

        renderdata = self._composer.compose(metatiles)

        ext = renderdata.data_type.ext
        mimetype = renderdata.data_type.mimetype
        metadata = dict(ext=ext, mimetype=mimetype, mtime=time.time())

        metatile = MetaTile.from_tile_index(metatile_index,
                                            renderdata.data,
                                            metadata)
        return metatile

    def close(self):
        pass
