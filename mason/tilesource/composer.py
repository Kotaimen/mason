'''
Created on May 21, 2012

@author: ray
'''
import time

from ..core import Tile, MetaTile
from ..utils import boxcrop, Timer
from .tilesource import TileSource
from ..tilelayer import StorageLayer


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

        # HACK: Support meta rendering only if there is no 'storage' source
        # TODO: 'sources' are actually instance of TileLayers... bad name
        for source in self._sources:
            if isinstance(source, StorageLayer):
                self._supports_metarendering = False
                break
        else:
            self._supports_metarendering = True

    def get_tile(self, tile_index):

        buffer_size = self._buffer_size

        # Get all tile layers
        layers = list()
        for n, source in enumerate(self._sources):
            # get tile from storage
#            with Timer('%s-Layer(#%d) generated in %%(time)s' % (tile_index, n)):
            layer = source.get_layer(tile_index, buffer_size)
            if layers is None:
                raise Exception('Invalid tile source #%d' % n)
            layers.append(layer)

        # Call composer to compose
#        with Timer('%s composed in %%(time)s' % (tile_index)):
        renderdata = self._composer.compose(layers)

        # Make data and metadata
        data = renderdata.data
        data_type = renderdata.data_type

        ext = data_type.ext
        mimetype = data_type.mimetype
        mtime = time.time()

        metadata = dict(ext=ext, mimetype=mimetype, mtime=mtime)

        # Crop from buffered image
        if buffer_size > 0:
            side = tile_index.pixel_size
            size = (side, side)

            left = top = buffer_size
            right = bottom = buffer_size + side

            cropbox = (left, top, right, bottom)
            data = boxcrop(data, ext, size, cropbox)

        # Create tile and return
        tile = tile_index.make_tile(data, metadata)
        return tile

    def get_metatile(self, metatile_index):

        """ Gets metatile """

        if self._supports_metarendering:
            return self.get_tile(metatile_index)

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
