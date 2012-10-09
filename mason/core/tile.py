"""
Tile object

Created on Apr 29, 2012
@author: Kotaimen
"""

import hashlib
import time

from .format import Format
from .geo import Envelope


class TileIndex(object):

    """ Coordinate & index of a Tile object """

    def __init__(self, pyramid, z, x, y):
        self._coord = z, x, y
        self._buffer = pyramid.buffer
        self._tile_size = pyramid.tile_size
        # Calculate envelope and serial so Tile can be detached from Pyramid
        self._envelope = pyramid.calculate_tile_envelope(z, x, y)
        self._buffered_envelope = pyramid.calculate_tile_buffered_envelope(z, x, y)
        self._serial = pyramid.calculate_tile_serial(z, x, y)

    @property
    def z(self):
        return self._coord[0]

    @property
    def x(self):
        return self._coord[1]

    @property
    def y(self):
        return self._coord[2]

    @property
    def coord(self):
        return self._coord

    @property
    def buffer(self):
        return self._buffer

    @property
    def envelope(self):
        return self._envelope

    @property
    def buffered_envelope(self):
        return self._buffered_envelope

    @property
    def serial(self):
        return self._serial

    @property
    def tile_size(self):
        return self._tile_size

    @property
    def buffered_tile_size(self):
        return self._tile_size + self._buffer * 2

    def __hash__(self):
        return hash(self._serial)

    def __cmp__(self, other):
        return self._serial - other._serial

    def __repr__(self):
        return 'TileIndex(%d/%d/%d)' % self._coord


class Tile(object):

    """ A map tile object

    Map tile contains three kinds of data::
    - Index describes geographic location of the tile
    - Binary data as string or bytes
    - Data format metadata
    - Tile Modification time

    Create Tile object using a Pyramid instance.
    """

    def __init__(self, index, data, fmt, mtime):
        assert isinstance(index, TileIndex)
        assert data is not None
        assert isinstance(data, bytes)
        self._index = index
        self._data = data
        self._format = fmt
        self._mtime = mtime
        # Calculate sha256 of binary data as hashing
        if self._data:
            self._hash = hashlib.sha256(self._data).hexdigest()
        else:
            # Empty data, use empty hex hashing string instead
            self._hash = ''

    @property
    def index(self):
        return self._index

    @property
    def data(self):
        return self._data

    @property
    def data_hash(self):
        return self._hash

    @property
    def format(self):
        return self._format

    @property
    def extension(self):
        return self._format['ext']

    @property
    def mimetype(self):
        return self._format['mimetype']

    @property
    def mtime(self):
        return self._mtime

    @staticmethod
    def from_tile_index(index, data, fmt=None, mtime=None):
        if fmt is None:
            fmt = Format.ANY
        if mtime is None:
            mtime = time.time()
        return Tile(index, data, fmt, mtime)

    def __repr__(self):
        return 'Tile(%d/%d/%d)' % self._index.coord


class MetaTileIndex(TileIndex):

    """ Coordinate index of a MetaTile object """

    def __init__(self, pyramid, z, x, y, stride):
        TileIndex.__init__(self, pyramid, z, x, y)

        self._stride = stride

        # A list of TileIndexes in the MetaTile 
        self._indexes = list()
        for i in range(x, x + stride):
            for j in range(y, y + stride):
                # Ignore range check and buffer here
                index = pyramid.create_tile_index(z, i, j,
                                                  range_check=False)
                self._indexes.append(index)

        z, x, y = self._coord
        left_bottom_index = pyramid.create_tile_index(z, x, y + stride - 1, range_check=False)
        right_top_index = pyramid.create_tile_index(z, x + stride - 1, y, range_check=False)
        left_bottom = left_bottom_index.envelope.leftbottom
        right_top = right_top_index.envelope.righttop
        self._envelope = Envelope(left_bottom.lon, left_bottom.lat,
                                  right_top.lon, right_top.lat)
        buffered_left_bottom = left_bottom_index._buffered_envelope.leftbottom
        buffered_right_top = right_top_index._buffered_envelope.righttop
        self._buffered_envelope = Envelope(buffered_left_bottom.lon,
                                           buffered_left_bottom.lat,
                                           buffered_right_top.lon,
                                           buffered_right_top.lat)

        # Overwrite tilesize
        self._tile_size = self._tile_size * stride

    @property
    def stride(self):
        return self._stride

    def fission(self):
        """ Get a list of TileIndexes belongs to the MetaTileIndex """
        return self._indexes

    def __repr__(self):
        return 'MetaTileIndex(%d/%d/%d@%d)' % (self.z, self.x, self.y, self.stride)


class MetaTile(Tile):

    """ Larger tile for render

    A MetaTile is square area contains adjacent Tiles and buffer
    to improve render speed.  A MetaTile always contains 2^nx2^n Tiles.
    """
    def __init__(self, index, data, fmt, ctime):
        Tile.__init__(self, index, data, fmt, ctime)
        assert isinstance(index, MetaTileIndex)

    @staticmethod
    def from_tile_index(index, data, fmt=None, mtime=None):
        if fmt is None:
            fmt = Format.ANY
        if mtime is None:
            mtime = time.time()
        return MetaTile(index, data, fmt, mtime)

    def __repr__(self):
        return 'MetaTile(%d/%d/%d@%d)' % (self.index.z, self.index.x,
                                          self.index.y, self.index.stride)
