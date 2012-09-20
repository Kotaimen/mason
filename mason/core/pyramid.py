""" Tile pyramid
Created on Apr 29, 2012

@author: Kotaimen
"""

import copy

from .tile import TileIndex, Tile, MetaTileIndex, MetaTile
from .geo import Envelope, Coordinate, create_projection, tile_coordinate_to_serial
from .format import Format

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
                 buffer=0,
                 format=Format.ANY,
                 envelope=(-180, -85.06, 180, 85.06),
                 center=(121.3, 31.1),
                 zoom=7,
                 crs='EPSG:4326',
                 proj='EPSG:3857',
                 ):
        """
        Create a new Pyramid object:

        levels
            Tile levels, a list of integers, note levels is not necessary
            continuous.

        tile_size
            Pixel size of a tile in the Pyramid, always a multiple of 256.

        buffer
            Render buffer size in pixel, default is 0, means no buffer is applied

        format
            Data format of tiles in the pyramid

        envelope
            Envelope of valid tile range in (left, bottom, right, top) tuple.
            Tiles outside this envelope cannot be created.

        center
            Center of the map in (lon, lat)

        zoom
            Default zoom level

        crs
            Authority ID of geography coordinate reference system, default is
            4326 (WGS84)

        proj
            Authority ID of map projection, default is 3857 (Google Mecartor)

        """
        assert levels
        assert (tile_size % 256) == 0
        assert buffer >= 0
        assert Format.is_known_format(format)
        assert zoom in levels

        self._levels = levels
        self._tile_size = tile_size
        self._buffer = buffer
        self._format = format

        self._envelope = Envelope.from_tuple(envelope)
        self._center = Coordinate.from_tuple(center)
        self._zoom = zoom
        self._crs = crs
        self._proj = proj
        self._projector = create_projection(input=self._crs,
                                            output=self._proj)

    # Getter ------------------------------------------------------------------

    @property
    def levels(self):
        return self._levels

    @property
    def tile_size(self):
        return self._tile_size

    @property
    def buffer(self):
        return self._buffer

    @property
    def format(self):
        return self._format

    @property
    def envelope(self):
        return self._envelope

    @property
    def center(self):
        return self._center

    @property
    def zoom(self):
        return self._zoom

    @property
    def projection(self):
        return self._proj

    # Aux Tile Methods ---------------------------------------------------------

    def calculate_tile_buffered_envelope(self, z, x, y):
        # XXX: This does not check whether tile is already clipping world boundary
        tile_size = self._tile_size
        buffer_size = self._buffer
        proj = self._projector

        envelope = proj.tile_envelope(z, x, y)

        lt_org = envelope.lefttop
        lt_org_pixel = proj.coord2worldpixel(lt_org, z, tile_size)
        rb_org = envelope.rightbottom
        rb_org_pixel = proj.coord2worldpixel(rb_org, z, tile_size)

        # left top coordinate
        lt_buf_lon = lt_org_pixel[0] - buffer_size
        lt_buf_lat = lt_org_pixel[1] - buffer_size
        lt_buf = proj.worldpixel2coord(z, lt_buf_lon, lt_buf_lat, tile_size)

        # right bottom coordinate
        rb_buf_lon = rb_org_pixel[0] + buffer_size
        rb_buf_lat = rb_org_pixel[1] + buffer_size
        rb_buf = proj.worldpixel2coord(z, rb_buf_lon, rb_buf_lat, tile_size)

        buffered = Envelope(left=lt_buf.lon, bottom=rb_buf.lat,
                            right=rb_buf.lon, top=lt_buf.lat)

        return buffered

    def calculate_tile_envelope(self, z, x, y):
        return self._projector.tile_envelope(z, x, y)

    def calculate_tile_serial(self, z, x, y):
        return tile_coordinate_to_serial(z, x, y)

    # Persistence --------------------------------------------------------------

    def summarize(self):
        return dict(
                    levels=self._levels,
                    tile_size=self._tile_size,
                    buffer=self._buffer,
                    format=self._format.make_dict(),
                    envelope=self._envelope.make_tuple(),
                    center=self._center.make_tuple(),
                    zoom=self._zoom,
                    crs=self._crs,
                    proj=self._proj
                    )

    def __repr__(self):
        return 'Pyramid%r' % self.summarize()

    @staticmethod
    def from_summary(summary):
        summary = dict(summary) # copy dict object
        summary['format'] = Format.from_dict(summary['format'])
        return Pyramid(**summary)

    def clone(self, format=None):
        new_object = copy.deepcopy(self)
        if format is not None:
            new_object._format = format
        return new_object

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

    def create_tile(self, z, x, y, data, mtime=None):
        tile_index = self.create_tile_index(z, x, y)
        return Tile.from_tile_index(tile_index, data, self.format, mtime)

    def create_metatile_index(self, z, x, y, stride):

        """ Create MetaTileIndex object using current pyramid & projection """

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

    def create_metatile(self, z, x, y, stride, data, mtime=None):
        tile_index = self.create_metatile_index(z, x, y, stride)
        return MetaTile.from_tile_index(tile_index, data, self.format, mtime)


