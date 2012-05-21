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
        assert mode in ['readonly', 'readwrite', 'overwrite']
        self._mode = mode

    @property
    def pyramid(self):
        return self._pyramid

    @property
    def tag(self):
        return self._tag

    @property
    def metadata(self):
        return self._metadata

    def get_tile(self, z, x, y):
        """ Get a tile from this layer, returns Tile object """
        tile_index = self._pyramid.create_tile_index(z, x, y)

        # Read from storage first
        if self._mode != 'overwrite':
            tile = self._storage.get(tile_index)
            if self._mode == 'readonly' or tile is not None:
                return tile

        # If misses, get a new one from source and put back to storage
        tile = self._source.get_tile(tile_index)
        self._storage.put(tile)

        return tile

    @staticmethod
    def dummy_logger(*args):
        pass

    def render_metatile(self, z, x, y, stride, logger=None):
        """ Render specified metatile and cache to storage if necessary """

        # Assign a dummy logger if none is given
        if logger is None:
            logger = self.dummy_logger
        else:
            logger = logger.debug

        # Create the metatile index
        metatile_index = self._pyramid.create_metatile_index(z, x, y, stride)
        # Although we can automatic fix MetaTileCoordinate, mismatching 
        # generally means something is wrong
        assert metatile_index.coord == (z, x, y)

        # Tag for debug output
        tag = 'MetaTile[%d/%d/%d@%d]' % (z, x, y, stride)

        # Fission into regular tiles indexes
        tile_indexes = metatile_index.fission()

        # Check whether required tiles are already rendered
        if self._mode != 'overwrite':
            with Timer('%s looked up in %%(time)s' % tag, logger, False):
                if self._storage.has_all(tile_indexes):
                    return False

        if self._mode == 'readonly':
            return False

        # Generate metatile and write all tiles to storage
        with Timer('%s rendered in %%(time)s' % tag, logger, False):
            metatile = self._source.get_metatile(metatile_index)
        tiles = metatile.fission()
        with Timer('%s saved in %%(time)s' % tag, logger, False):
            self._storage.put_multi(tiles)

        return True

    def close(self):
        if self._source is not None:
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
                 mode='readonly',
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

    mode
        Operation mode, can be one of "readonly", "readwrite", "rewrite".
        "readonly" reads everything from TileStorage and never renders
        "overwrite" renders from TileSource and write to TileStorage every time
        "readwrite" read from TileStorage if it already exists, and render
                    a new one, cache into storage otherwise

    source
        TileSource configuration, see TileSource docs

    storage
        TileStorage configuration, see TileStorage docs

    metadata
        Metadata as a dict

    """

    # Create Pyramid Object
    pyramid = Pyramid(levels=levels,
                      tile_size=tile_size,
                      envelope=envelope,
                      crs=crs,
                      proj=proj
                      )

    if source is None and storage is None:
        raise Exception('source and storage cannot both be None')

    # create source object
    if source is None:
        source_object = None
    else:
        source_config = dict(source)
        if 'tag' not in source_config:
            source_config['tag'] = tag
        source_object = TileSourceFactory()(**source_config)

    # create storage object
    if storage is None:
        storage_config = {'prototype': 'null', 'tag': tag}
    else:
        storage_config = dict(storage)
        if 'tag' not in storage_config:
            storage_config['tag'] = tag
    storage_object = TileStorageFactory()(**storage_config)

    # create metadata
    metadata.update(dict(name=tag,
                         extension=ext,
                         mimetype=mimetype,
                         levels=levels,
                         envelope=envelope,
                         center=center,
                         crs=crs,
                         projection=proj))

    return Layer(tag, pyramid, source_object, storage_object, metadata,
                 mode=mode)
