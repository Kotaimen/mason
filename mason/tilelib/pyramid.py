'''
Created on Apr 29, 2012

@author: Kotaimen
'''

from .tile import TileIndex, Tile, MetaTileIndex, MetaTile
from . import geo

#===============================================================================
# Exceptions
#===============================================================================


class TileOutOfRange(Exception):
    pass


class InvalidTileParameter(Exception):
    pass


class Pyramid(object):

    """ Represents a quad-tree structure of tile Pyramid

    Hides geography calculations behind this class.  Also being a factory of
    TileIndex/Tile object.
    """

    def __init__(self,
                 levels=list(range(0, 11)),
                 tile_size=256,
                 envelope=(-180, -85.06, 180, 85.06),
                 crs='ESPG:4326',
                 proj='ESPG:3857',
                 ):
        """
        Create a new Pyramid object, arguments:

        level
            Tile levels, a list of integers, note levels is not necessary
            continuous.

        tile_size
            Pixel size of a tile in the Pyramid, always a multiple of 256.

        envelope
            Envelope of valid tile range in (left, bottom, right, top) tuple.
            Tiles outside this envelope cannot be created.

        crs
            Authority ID of geography coordinate reference system, default is
            4326 (WGS84)

        proj
            Authority ID of map projection, default is 3857 (Google Mecartor)

        """
        assert levels
        assert (tile_size % 256) == 0
        self._levels = levels
        self._tile_size = tile_size
        self._envelope = geo.Envelope.from_tuple(envelope)
        self._crs = crs
        self._proj = proj

        self._projector = geo.create_projection(input=self._crs,
                                                output=self._proj)

    @property
    def levels(self):
        return self._levels

    @property
    def tile_size(self):
        return self._tile_size

    @property
    def envelope(self):
        return self._envelope

    @property
    def projection(self):
        return self._proj

    @property
    def projector(self):
        return self._projector

    def calculate_tile_envelope(self, z, x, y):
        return self._projector.tile_envelope(z, x, y)

    def calculate_tile_serial(self, z, x, y):
        return geo.tile_coordinate_to_serial(z, x, y)

    # Tile Factory Methods -----------------------------------------------------

    def create_tile_index(self, z, x, y, range_check=True):
        """ Create TileIndex object using current pyramid projection and range
        constraints """

        if z not in self._levels:
            raise TileOutOfRange('Invalid layer "%d"' % z)

        # Adjust tile coordinate if tile is out of cover range
        dim = 2 ** z
        if x < 0 or x >= dim:
            x = x % dim
        if y < 0 or y >= dim:
            y = y % dim

        tile_index = TileIndex(self, z, x, y)
        if range_check and not tile_index.envelope.intersects(self._envelope):
            raise TileOutOfRange('Tile out of range')

        return tile_index

    def create_tile(self, z, x, y, data, metadata):

        """ Create a Tile object using given coordinate, data and metadata """

        if not isinstance(data, bytes):
            raise InvalidTileParameter('Except a bytes object as tile data')
        if not isinstance(metadata, dict):
            # XXX: ensure metadata as literal using ast
            raise InvalidTileParameter('Except dict object as tile metadata')

        return Tile(self.create_tile_index(z, x, y),
                    data,
                    metadata)

    def create_metatile_index(self, z, x, y, stride):

        """ Create MetaTileIndex object using current pyramid projection """

        if stride < 1 or stride & (stride - 1) != 0:
            raise InvalidTileParameter('stride must be power of 2, got %d',
                                       stride)
        dim = 2 ** z

        # Adjust coordinate if tile is out of range
        if x < 0 or x >= dim:
            x = x % dim
        if y < 0 or y >= dim:
            y = y % dim

        # Move coordinate to left top tile in the meta tile
        x -= (x % stride)
        y -= (y % stride)

        # Adjust if stride is too large for current layer
        if (stride >> z) > 0:
            stride = dim

        return MetaTileIndex(self, z, x, y, stride)

    def create_dummy_metatile(self, z, x, y, stride, tiles):
        if len(tiles) != stride * stride:
            raise InvalidTileParameter('Invalid tiles for dummy metatile')

        index = self.create_metatile_index(z, x, y, stride)

        if set(index.fission()) != set(t.index for t in tiles):
            raise InvalidTileParameter('Invalid tiles for dummy metatile')

        return MetaTile(index, tiles, metadata=dict())

    def create_metatile(self, z, x, y, stride, data, metadata):
        index = self.create_metatile_index(z, x, y, stride)
        return MetaTile.from_tile_index(index, data, metadata)


