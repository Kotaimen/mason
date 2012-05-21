'''
Created on May 21, 2012

@author: ray
'''
import time
import mimetypes

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

        ext = self._composer.data_type
        if ext.startswith('png'):
            ext = 'png'
        elif ext.lower().endswith('tiff'):
            ext = 'tif'
        elif ext.lower() == 'jpeg':
            ext = 'jpg'
        mimetype = mimetypes.guess_type('ext.%s' % ext)[0]
        self._metadata = dict(ext=ext, mimetype=mimetype)

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

        data = self._composer.compose(tiles)

        metadata = dict(self._metadata)
        metadata['mtime'] = time.time()

        tile = Tile.from_tile_index(tile_index, data, metadata)
        return tile

    def get_metatile(self, metatile_index):
        """ Gets metatile """

        metatiles = list()

        for source in self._sources:
            metatile = source.get_metatile(metatile_index)
            if metatile is not None:
                metatiles.append(metatile)

        data = self._composer.compose(metatiles)

        metadata = dict(self._metadata)
        metadata['mtime'] = time.time()

        metatile = MetaTile.from_tile_index(metatile_index, data, metadata)
        return metatile
