'''
Created on Apr 29, 2012

@author: Kotaimen
'''

import hashlib
import warnings

try:
    from ..utils import gridcrop
except ImportError:
    warnings.warn("Can't import mason.utils.gridcrop, install PIL/imagemagick")
    def gridcrop(*args):
        raise NotImplementedError

from .geo import Envelope


class TileIndex(object):

    """ Coordinate index of a Tile object """

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

    Create Tile object using a Pyramid instance.

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

    def __init__(self, index, data, metadata):
        assert isinstance(index, TileIndex)
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
    def datahash(self):
        return self._hash

    @staticmethod
    def from_tile_index(index, data, metadata):
        return Tile(index, data, metadata)

    def __repr__(self):
        return 'Tile(%d/%d/%d)' % self._index.coord


class MetaTileIndex(TileIndex):

    """ Coordinate index of a MetaTile object

    A MetaTile is rectangular area of adjacent Tiles used to improve
    render speed, render in large images reduces database and buffer
    overhead.
    """

    def __init__(self, pyramid, z, x, y, stride):
        TileIndex.__init__(self, pyramid, z, x, y)

        self._stride = stride
        self._pyramid = pyramid

        # A list of TileIndexes in the MetaTile
        self._indexes = list()
        for i in range(x, x + stride):
            for j in range(y, y + stride):
                self._indexes.append(pyramid.create_tile_index(z, i, j,
                                                              range_check=False))

        # Modify properties calculated in base class
        z, x, y = self._coord
        left_bottom = self._indexes[0].envelope.leftbottom
        right_top = self._indexes[-1].envelope.righttop
        self._envelope = Envelope(left_bottom.lon, left_bottom.lat,
                                  right_top.lon, right_top.lat)
        self._pixsize = self._pixsize * stride

    @property
    def stride(self):
        return self._stride

    def fission(self):
        """ Get a list of TileIndexes belongs to the MetaTileIndex """
        return self._indexes


class MetaTile(Tile):

    def __init__(self, index, tiles, data=None):
        if data is None:
            data = b''
        Tile.__init__(self, index, data, {})
        assert isinstance(index, MetaTileIndex)
        self._tiles = tiles

    def fission(self):
        return self._tiles

    @staticmethod
    def from_tile_index(metatile_index, data, metadata):
        # Gridcrop really need to know image type
        ext = metadata['ext']
        if ext not in {'png', 'jpg', 'tif'}:
            raise Exception('Sorry, only supports PNG/JPEG/TIFF image files')

        z, x, y = metatile_index.coord
        stride = metatile_index.stride
        pyramid = metatile_index._pyramid

        # Crop into grids, returns {(i, j): data}
        tile_datas = gridcrop(data, stride, stride, ext=ext)

        tiles = list()
        for (i, j), data in tile_datas.iteritems():
            tile = pyramid.create_tile(z, x + i, y + j, data, metadata)
            tiles.append(tile)
        return MetaTile(metatile_index, tiles, data)

