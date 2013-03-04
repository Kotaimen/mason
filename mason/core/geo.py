"""
Geographic calculations

Created on Apr 30, 2012
@author: Kotaimen
"""
import re
import osr
import math
import collections
import shapely.geometry


#===============================================================================
# Spatial Reference System
#===============================================================================
class InvalidSRID(Exception):
    pass


class SRID(object):

    """ Spatial Reference System Identifier

    @param param: authority name of srid
    @param param: integer code of srid
    """

    __slots__ = '_authority', '_code'

    def __init__(self, authority, code):
        self._authority = authority.upper()
        self._code = int(code)

    @property
    def authority(self):
        return self._authority

    @property
    def code(self):
        return self._code

    def make_tuple(self):
        return (self._authority, self._code)

    @staticmethod
    def from_string(srid_string):
        """ srid format: 'authority:code' """
        m = re.match('(?P<authority>\w+):(?P<code>\d+)', srid_string)
        if not m:
            raise InvalidSRID(srid_string)
        authority = m.group('authority')
        code = m.group('code')
        return SRID(authority, code)

    def to_string(self):
        return str(self)

    def __str__(self):
        return '%s:%s' % (self.authority, self.code)

    def __repr__(self):
        return '%s(%r, %s)' % (self.__class__.__name__,
                               self._authority,
                               self._code)

    def __eq__(self, other):
        return self.make_tuple() == other.make_tuple()


def create_osr_spatial_ref(srid):
    """ Create osr spatial reference from srid
    """
    assert isinstance(srid, SRID)
    authority, code = srid.make_tuple()
    reference = osr.SpatialReference()
    if 'EPSG' == authority.upper():
        reference.ImportFromEPSG(code)
    else:
        # only support EPSG now.
        raise NotImplementedError
    return reference


class SpatialReference(object):

    """ Spatial Reference System

    @param srid: the srid of the spatial reference
    """

    def __init__(self, srid):

        reference = create_osr_spatial_ref(srid)

        # set datum parameters
        self._srid = srid
        self._semi_major = reference.GetSemiMajor()
        self._semi_minor = reference.GetSemiMinor()
        self._flatten_factor = 1 - self._semi_minor / self._semi_major

    @property
    def srid(self):
        return self._srid

    @property
    def semi_major(self):
        return self._semi_major

    @property
    def semi_minor(self):
        return self._semi_minor

    @property
    def flattening(self):
        return self._flatten_factor


class SpatialTransformer(object):

    """ Spatial Reference System Transformer

    Transform coordinates from source to target spatial reference system

    @param src_srid: srid of source spatial reference system
    @param dst_srid: srid of target spatial reference system
    """

    def __init__(self, src_srid, dst_srid):
        source = create_osr_spatial_ref(src_srid)
        target = create_osr_spatial_ref(dst_srid)

        self._forward = osr.CoordinateTransformation(source, target)
        self._reverse = osr.CoordinateTransformation(target, source)

    def forward(self, x, y, z=0):
        x, y, z = self._forward.TransformPoint(x, y, z)
        return x, y, z

    def reverse(self, x, y, z=0):
        x, y, z = self._reverse.TransformPoint(x, y, z)
        return x, y, z


#===============================================================================
# Geographic Primitives
#===============================================================================
class Location(object):

    """ Geographic Location """

    __slots__ = '_lon', '_lat', '_alt'

    def __init__(self, lon=0.0, lat=0.0, alt=0.0):
        self._lon = lon
        self._lat = lat
        self._alt = alt

    @property
    def lon(self):
        return self._lon

    @property
    def lat(self):
        return self._lat

    @property
    def alt(self):
        return self._alt

    def make_tuple(self):
        return (self._lon, self._lat, self._alt)

    @staticmethod
    def from_tuple(t):
        return Location(*t)

    def __repr__(self):
        return '%s(%s, %s, %s)' % (self.__class__.__name__,
                                   self._lon,
                                   self._lat,
                                   self._alt,
                                   )

    def __eq__(self, other):
        return self.make_tuple() == other.make_tuple()


class Envelope(object):

    """ A geographic bounding box

    Envelope is not supposed to cross -180/180 longitude
    """

    __slots__ = '_minx', '_miny', '_maxx', '_maxy',

    def __init__(self, minx, miny, maxx, maxy):
        self._minx = minx
        self._miny = miny
        self._maxx = maxx
        self._maxy = maxy

    @property
    def left(self):
        return self._minx

    @property
    def bottom(self):
        return self._miny

    @property
    def right(self):
        return self._maxx

    @property
    def top(self):
        return self._maxy

    @property
    def lefttop(self):
        return Location(self._minx, self._maxy, 0)

    @property
    def righttop(self):
        return Location(self._maxx, self._maxy, 0)

    @property
    def leftbottom(self):
        return Location(self._minx, self._miny, 0)

    @property
    def rightbottom(self):
        return Location(self._maxx, self._miny, 0)

    def make_geometry(self):
        return shapely.geometry.box(self._minx, self._miny, self._maxx, self._maxy)

    def intersects(self, other):
        """ Checks whether the envelop intersects with given one """
        return self.make_geometry().intersects(other.make_geometry())

    def make_tuple(self):
        return (self._minx, self._miny, self._maxx, self._maxy)

    @staticmethod
    def from_tuple(t):
        return Envelope(*t)

    def __repr__(self):
        return 'Envelope(%s, %s, %s, %s)' % (self._minx,
                                             self._miny,
                                             self._maxx,
                                             self._maxy
                                            )

    def __eq__(self, other):
        return self.make_tuple() == other.make_tuple()


#===============================================================================
# Projection Primitives
#===============================================================================
class Point2D(collections.namedtuple('Point', 'x y')):
    pass


class WGS84Projector(object):

    WGS84 = SRID.from_string('epsg:4326')

    def __init__(self, proj_srid):
        self._proj_srid = SRID.from_string(proj_srid)
        self._transformer = SpatialTransformer(self.WGS84, self._proj_srid)

    def project(self, location):
        lon, lat, alt = location.make_tuple()
        x, y, _z = self._transformer.forward(lon, lat, alt)
        return Point2D(x, y)

    def unproject(self, point):
        x, y = point
        lon, lat, _alt = self._transformer.reverse(x, y, 0)
        return Location(lon, lat)


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




