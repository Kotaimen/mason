'''
Created on Apr 29, 2012

@author: Kotaimen
'''

import hashlib

class TileIndex(object):

    """ Coordinate index of a Tile object """

    __slots__ = '_coord', '_envelope', '_serial', '_shard', '_pixsize'

    def __init__(self, pyramid, z, x, y):
        self._coord = z, x, y
        # Calculate envelope and serial so Tile can be detached from Pyramid
        self._envelope = pyramid.calculate_tile_envelope(z, x, y)
        self._serial = pyramid.calculate_tile_serial(z, x, y)
        self._pixsize = pyramid.tile_size
        # TODO: implement sharding hash 
        self._shard = 0

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
    def envelope(self):
        return self._envelope

    @property
    def serial(self):
        return self._serial

    @property
    def pixel_size(self):
        return self._pixsize

    def __hash__(self):
        return hash(self._serial)

    def __cmp__(self, other):
        return self._serial - other._serial


class Tile(object):

    """ A map tile object

    Map tile contains three kinds of data::
    - Index describes geographic location of the tile
    - Data, which is the tile attached binary data, usually bytes/str
    - A dictionary as metadata, describes additional tile information as
      key-value pairs

    Tile object is immutable once created.



    Note: in Python 2.x, data is a str, in Python3.x, data is a
          byte string (bytes)

    Metadata is optional, but usually frontend http server requires some
    fields to produce a meaningful http response:

    mimetype
        String, the mimetype of tile data, eg: 'application/json'

    ext
        String, filename extension of tile data, eg: 'png'

    mtime
        String, ISO format time of last tile modification time

    """

    __slots__ = '_index', '_data', '_metadata', '_hash'

    def __init__(self, index, data, metadata):
        assert isinstance(index, TileIndex)
        assert isinstance(data, bytes)  # works on 2.7-3.x
        assert isinstance(metadata, dict)  # don't care what's in the dict
        self._index = index
        self._data = data
        self._metadata = metadata

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
    def metadata(self):
        return self._metadata

    @property
    def hash(self):
        return self._hash

    @staticmethod
    def from_tile_index(index, data, metadata):
        return Tile(index, data, metadata)

    def __repr__(self):
        return 'Tile(%d/%d/%d)' % self._index.coord


class MetaTile(object):

    pass
