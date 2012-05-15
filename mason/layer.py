'''
Created on May 14, 2012

@author: Kotaimen
'''

from .tilesource import TileSourceFactory
from .tilestorage import TileStorageFactory
from .tilelib import Pyramid
from .utils import Timer


class Layer(object):

    """ A layer of tiles """

    def __init__(self,
                 tag,
                 pyramid,
                 source,
                 storage,
                 metadata,
                 mode='readonly',
                 ):
        self._tag = tag
        self._pyramid = pyramid
        self._source = source
        self._storage = storage
        self._metadata = metadata
        assert mode in ['default', 'readonly', 'rewrite']
        self._mode = mode

    @property
    def tag(self):
        return self._tag

    @property
    def metadata(self):
        return self._metadata

    def get_tile(self, z, x, y):

        tile_index = self._pyramid.create_tile_index(z, x, y)

        # Read from storage first
        if self._mode != 'rewrite':
            tile = self._storage.get(tile_index)
            if self._mode == 'readonly' or tile is not None:
                return tile

        # If misses, get a new one from source and put back to storage
        tile = self._source.get_tile(tile_index)
        self._storage.put(tile)

        return tile

    def render_metatile(self, z, x, y, stride):
        metatile_index = self._pyramid.create_metatile_index(z, x, y, stride)
        # Although we can automatic fix MetaTileCoordinate, mismatching 
        # generally means something is wrong
        assert metatile_index.coord == (z, x, y)

        tile_indexes = metatile_index.fission()
        # Check whether tiles are all rendered
        if self._mode != 'rewrite':
            if self._storage.has_all(tile_indexes):
                return

        if self._mode == 'readonly':
            return

        # Generate metatile and write all tiles to storage
        metatile = self._source.get_metatile(metatile_index)
        tiles = metatile.fission()
        self._storage.put_multi(tiles)

    def close(self):
        self._source.close()
        self._storage.close()


def create_layer(tag,
                 ext='png',
                 mimetype='image/png',
                 levels=range(0, 21),
                 tile_size=256,
                 envelope=(-180, -85.06, 180, 85.06),
                 center=(0, 0),
                 crs='EPSG:4326',
                 proj='ESPG:3857',
                 mode='default',
                 source={},
                 storage={},
                 metadata={},
                 ):
    """ Create a Layer object

    tag
        Name of the layer, must be valid Python identifier

    ext
        File extension of the tile, eg "png"

    mimetype
        mimetype of the tile

    tile_size
        Pixel size of tile images

    levels
        A list of valid layers

    envelope
        Envelope of valid tile range in (left, bottom, right, top)

    center
        Center point of tile range

    crs
        Authority ID of geography coordinate reference system

    proj
        Authority ID of map projection

    """

    # Create Pyramid Object
    pyramid = Pyramid(levels=levels,
                      tile_size=tile_size,
                      envelope=envelope,
                      crs=crs,
                      proj=proj
                      )

    if source is None:
        source_object = None
    else:
        source_config = dict(source)
        source_object = TileSourceFactory()(**source)

    storage_config = dict(storage)
    if 'tag' not in storage_config:
        storage_config['tag'] = tag
    storage = TileStorageFactory()(**storage_config)

    metadata.update(dict(name=tag,
                         extension=ext,
                         mimetype=mimetype,
                         levels=levels,
                         envelope=envelope,
                         center=center,
                         crs=crs,
                         projection=proj))

    return Layer(tag, pyramid, source, storage, metadata,
                 mode=mode)

