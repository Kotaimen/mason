""" Tile pyramid
Created on Apr 29, 2012

@author: Kotaimen
"""

import copy
import math
from .tile import TileIndex, Tile, MetaTileIndex, MetaTile
from .geo import Envelope, Location, tile_coordinate_to_serial
from .geo import SRID, Datum, SpatialTransformer
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
                 zoom=None,
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

        crs (deprecated)
            Authority ID of geography coordinate reference system, default is
            4326 (WGS84)

        proj
            Authority ID of map projection, default is 3857 (Google Mecartor)

        """
        assert levels
        assert (tile_size % 256) == 0
        assert buffer >= 0
        assert Format.is_known_format(format)

        zoom = levels[0] if zoom is None else zoom
        assert zoom in levels

        self._levels = levels
        self._tile_size = tile_size
        self._buffer = buffer
        self._format = format
        self._zoom = zoom

        self._proj_srid = SRID.from_string(proj)
        # internal spatial reference id
        self._wgs84 = SRID.from_string('EPSG:4326')

        minx, miny, maxx, maxy = envelope
        self._envelope = Envelope.from_tuple((minx, miny, maxx, maxy, self._wgs84))

        lon, lat = center
        self._center = Location.from_tuple((lon, lat, 0, self._wgs84))

        # datum of the projection
        self._datum = Datum(self._proj_srid)
        self._perimeter = 2 * math.pi * self._datum.semi_major

        # projection between internal srid and specified srid
        self._projctor = SpatialTransformer(self._wgs84, self._proj_srid)

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
    def coords_xyz2world(self, z, x, y, delta_x, delta_y):
        wx = float(x + delta_x) / (2 ** z)
        wy = float(y + delta_y) / (2 ** z)
        return wx, wy

    def coords_world2xyz(self, z, wx, wy):
        total = 2 ** z
        x, y = (int(math.floor(total * wx)),
                int(math.floor(total * wy)))
        if x < 0:
            x = 0
        if y < 0:
            y = 0
        if x >= total:
            x = total - 1
        if y >= total:
            y = total - 1

        return x, y

    def coords_world2pixel(self, z, wx, wy):
        pixel_size = self._tile_size * (2 ** z)
        px = wx * pixel_size
        py = wy * pixel_size
        return px, py

    def coords_pixel2world(self, z, px, py):
        pixel_size = self._tile_size * (2 ** z)
        wx = px / pixel_size
        wy = py / pixel_size
        return wx, wy

    def coords_world2wgs84(self, z, wx, wy):
        perimeter = self._perimeter
        wx = (wx - 0.5) * perimeter
        wy = (0.5 - wy) * perimeter
        lon, lat, _alt = self._projctor.reverse(wx, wy, 0)
        return lon, lat

    def coords_wgs842world(self, z, lon, lat):
        wx, wy, _wz = self._projctor.forward(lon, lat)
        perimeter = self._perimeter
        wx = wx / perimeter
        wy = wy / perimeter
        return wx, wy

    def coords_wgs842xyz(self, z, lon, lat):
        wx, wy = self.coords_wgs842world(z, lon, lat)
        return self.coords_world2xyz(z, wx, wy)

    def coords_xyz2wgs84(self, z, x, y):
        wx, wy = self.coords_xyz2world(z, x, y, 0, 0)
        return self.coords_world2wgs84(z, wx, wy)

    def calculate_tile_buffered_envelope(self, z, x, y):

        buff_size = self._buffer

        wminx, wminy = self.coords_xyz2world(z, x, y, 0, 1)
        wmaxx, wmaxy = self.coords_xyz2world(z, x, y, 1, 0)

        pminx, pminy = self.coords_world2pixel(z, wminx, wminy)
        pmaxx, pmaxy = self.coords_world2pixel(z, wmaxx, wmaxy)

        # expand envelope with buffer size
        buffpminx, buffpminy = pminx - buff_size, pminy - buff_size
        buffpmaxx, buffpmaxy = pmaxx + buff_size, pmaxy + buff_size

        buffwminx, buffwminy = self.coords_pixel2world(z, buffpminx, buffpminy)
        buffwmaxx, buffwmaxy = self.coords_pixel2world(z, buffpmaxx, buffpmaxy)

        # transform to wgs84
        minx, miny = self.coords_world2wgs84(z, buffwminx, buffwminy)
        maxx, maxy = self.coords_world2wgs84(z, buffwmaxx, buffwmaxy)

        return Envelope(minx, miny, maxx, maxy, srid=self._wgs84)

    def calculate_tile_envelope(self, z, x, y):

        minx, miny = self.coords_xyz2wgs84(z, x, y + 1)
        maxx, maxy = self.coords_xyz2wgs84(z, x + 1, y)

        return Envelope(minx, miny, maxx, maxy, srid=self._wgs84)

    def calculate_tile_serial(self, z, x, y):
        return tile_coordinate_to_serial(z, x, y)

    # Persistence --------------------------------------------------------------

    def summarize(self):
        return dict(
                    levels=self._levels,
                    tile_size=self._tile_size,
                    buffer=self._buffer,
                    format=self._format.make_dict(),
                    envelope=self._envelope.coords(),
                    center=self._center.coords(),
                    zoom=self._zoom,
#                    crs=self._wgs84.to_string(),
                    proj=self._proj_srid.to_string()
                    )

    def __repr__(self):
        return 'Pyramid%r' % self.summarize()

    @staticmethod
    def from_summary(summary):
        summary = dict(summary)  # copy dict object
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


