'''
Created on Apr 30, 2012

@author: Kotaimen
'''

import collections
import math

#===============================================================================
# Geography Primitives
#===============================================================================


class Coordinate(object):

    """ Geographic location """

    __slots__ = '_longitude', '_latitude', '_crs'

    def __init__(self, longitude=0.0, latitude=0.0, crs='ESPG:4326'):
        self._longitude = longitude
        self._latitude = latitude
        self._crs = crs

    @property
    def longitude(self):
        return self._longitude

    @property
    def latitude(self):
        return self._latitude

    # Shorthand
    lon = longitude
    lat = latitude

    @property
    def crs(self):
        return self._crs

    def make_tuple(self):
        return (self._longitude, self._latitude)

    @staticmethod
    def from_tuple(t):
        return Coordinate(*t)

    def __repr__(self):
        return '%s(%s, %s)' % (self.__class__.__name__, self._longitude, self._latitude)

    def __eq__(self, other):
        return self.make_tuple() == other.make_tuple()


class Envelope(object):

    """ A geographic bounding box

    Envelope is not supposed to cross -180/180 longitude
    """

    __slots__ = '_left', '_bottom', '_right', '_top', '_crs'

    def __init__(self, left, bottom, right, top, crs='ESPG:4326'):
        self._left = left
        self._bottom = bottom
        self._right = right
        self._top = top
        self._crs = crs

    @property
    def left(self):
        return self._left

    @property
    def bottom(self):
        return self._bottom

    @property
    def right(self):
        return self._right

    @property
    def top(self):
        return self._top

    @property
    def crs(self):
        return self._crs

    @property
    def lefttop(self):
        return Coordinate(self._left, self._top, self._crs)

    @property
    def righttop(self):
        return Coordinate(self._right, self._top, self._crs)

    @property
    def leftbottom(self):
        return Coordinate(self._left, self._bottom, self._crs)

    @property
    def rightbottom(self):
        return Coordinate(self._right, self._bottom, self._crs)

    def contains(self, coordinate):
        """ Checks whether the envelop contains the given point """
        assert self.crs == coordinate.crs
        return coordinate.lon >= self.left and coordinate.lon <= self.right \
            and coordinate.lat >= self.bottom and coordinate.lat <= self.top

    def intersects(self, other):
        """ Checks whether the envelop intersects with given one """
        assert self.crs == other.crs
        # Stupid brute force implement ...don't want depend on a geographic
        # library (eg: django.contrib.geodjango) here
        other_corners = (other.lefttop, other.righttop, other.leftbottom,
                         other.rightbottom)
        this_corners = (self.lefttop, self.righttop,
                        self.leftbottom, self.rightbottom)
        return any(self.contains(p) for p in other_corners) or \
               any(other.contains(p) for p in this_corners)

    def make_tuple(self):
        return (self._left, self._bottom, self._right, self._top)

    @staticmethod
    def from_tuple(t):
        return Envelope(*t)

    def __repr__(self):
        return 'Envelope(%r)' % (self.make_tuple())

    def __eq__(self, other):
        return self.make_tuple() == other.make_tuple()


class Point(collections.namedtuple('Point', 'x y')):

    """ Point, a standard namedtuple application """

    pass

#===============================================================================
# Projection
#===============================================================================


class GoogleMercatorProjection(object):

    """ Project ESPG:4326 (WGS84) to ESPG:3857 (Google Mercator)

    The defacto standard web map projection Google Mercator is formerly
    known as ESPG:900913, which is a actually a joke for "google", so in
    PostGIS 2.0 the projections is replaced by standard name ESPG:3857.

    Note: This is reinvented so we don't have to depend on gdal-python
    when just deploying a read only tile server.
    """

    def __init__(self):
        self.name = 'Google Mercator'
        self.crs = 'ESPG:3857'

    def project(self, coordinate):
        """ Project a WGS84 coordinate to GoogleMercator

        Note the result point is in normalized ((0, 0), (1, 1)) plane.
        """
        assert coordinate.crs == 'ESPG:4326'
        lon, lat = coordinate.make_tuple()
        x = lon / 360. + 0.5
        y = math.log(math.tan(math.pi / 4. + math.radians(lat) / 2.))
        y = 0.5 - y / 2. / math.pi
        return Point(x, y)

    def unproject(self, point):
        """ Unproject a GoogleMercator point back to WSG84 """

        x, y = point
        lon = (x - 0.5) * 360.
        lat = math.degrees(2 * math.atan(math.exp((1. - 2. * y) * math.pi)) - \
                           math.pi / 2.)
        return Coordinate(lon, lat)

    def coord2tile(self, coordinate, z):
        """ Coordinate to tile """
        world_x, world_y = self.project(coordinate)
        tile_num = 2 ** z
        x, y = (int(math.floor(tile_num * world_x)),
                int(math.floor(tile_num * world_y)))
        if x < 0:
            x = 0
        if y < 0:
            y = 0
        if x >= tile_num:
            x = tile_num - 1
        if y >= tile_num:
            y = tile_num - 1

        return x, y

    def coord2pixel(self, coordinate, z, tile_size=256):

        world_x, world_y = self.project(coordinate)

        pixel_size = 2 ** z * tile_size  # total pixel size
        pixel_x = world_x * pixel_size
        pixel_y = world_y * pixel_size

        return pixel_x % tile_size, pixel_y % tile_size

    def pixel2coord(self, z, x, y, pixel_x, pixel_y, tile_size=256):
        wx = (x * tile_size + pixel_x) / (2 ** z * tile_size)
        wy = (y * tile_size + pixel_y) / (2 ** z * tile_size)
        return self.unproject(Point(wx, wy))

    def tile_envelope(self, z, x, y):
        left_bottom = self.pixel2coord(z, x, y, 0., 1., 1.)
        right_top = self.pixel2coord(z, x, y, 1., 0., 1.)
        return Envelope(left=left_bottom.lon, bottom=left_bottom.lat,
                        right=right_top.lon, top=right_top.lat)


def create_projection(input, output, **args):
    """ Dummy factory function, in case other projection is added later """
    # Only supports WGS84 lonlat to GoogleMecartor projection
    assert input == 'ESPG:4326' and output == 'ESPG:3857'
    return GoogleMercatorProjection()


#===============================================================================
# Tile Coordinates
#===============================================================================


def tile_coordinate_to_serial(z, x, y):
    """ Convert tile coordinate to an integer serial

    Flatten tile coordinate (z, x, y) to a serial by::

        (4^(z)-1) / 3 + 2^z * y + x

    This formula is calculated form total number of tiles of layer 0~k::

        Sum[4^n, {n, 0, k}] = (4^(k+1)-1) / 3


    For a 32 bit integer serial, the largest supported tile layer is 15.
    For a 64 bit integer serial, the largest supported tile layer is 31.

    """
    # Limit serial to 64 bit signed integer
    assert z >= 0 and z <= 30
    # Number of tile per axis
    dim = 2 ** z
    assert x < dim and x >= 0 and y < dim and y >= 0

    return (4 ** z - 1) // 3 + y * dim + x


def tile_coordiante_to_dirname(z, x, y, m=64):

    """ Return a directory tree path for a given tile coordinate

    Groups adjacent m*m tiles in a sub directory to improve file system
    performance.  Returns a list of directory names, to create a directory str,
    use os.path.join(*list)
    """

    assert z >= 0 and z <= 31
    dim = 2 ** z
    assert x < dim and x >= 0 and y < dim and y >= 0

    zdiff = int(math.floor(math.log(m) / math.log(2)))

    # layer has less than m*m tiles, just use z as pathname
    if z <= zdiff:
        return ['%02d' % z, ]

    # metatile number
    mx, my = x // m, y // m
    mz = z - zdiff
    mn = 2 ** mz * my + mx

    # calculate how many digits are needed
    digits = len('%x' % (4 ** mz - 1))
    if digits % 2 != 0:
        digits += 1
    hex_str = ('%%0%dX' % digits) % mn

    # split hex string into 2 char tuple 
    dirs = list((hex_str[i:i + 2] for i in range(0, len(hex_str), 2)))
    dirs.insert(0, '%02d' % z)

    return dirs


def tile_coordinate_to_sharding_index(z, x, y, m=64):

    raise NotImplementedError




