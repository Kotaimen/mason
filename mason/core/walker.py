"""
Iterate over a Pyramid and generate TileIndexes

Created on Aug 31, 2012
@author: Kotaimen
"""

from .geo import GoogleMercatorProjection, Envelope

import csv


class PyramidWalker(object):

    def __init__(self, pyramid, levels=None, stride=1, envelope=None):
        self._pyramid = pyramid
        if levels is not None:
            self._levels = levels
        else:
            self._levels = pyramid.levels
        if envelope is not None:
            self._envelope = Envelope.from_tuple(envelope)
        else:
            self._envelope = pyramid.envleope
        self._stride = stride
        assert pyramid.projection == 'EPSG:3857'
        self._proj = GoogleMercatorProjection()

    def walk(self):
        stride = self._stride
        for z in self._levels:
            left, top = self._proj.coord2tile(self._envelope.lefttop, z)
            right, bottom = self._proj.coord2tile(self._envelope.rightbottom, z)

            x_min = left // stride * stride
            y_min = top // stride * stride

            x_max = ((right // stride) + 1) * stride
            y_max = ((bottom // stride) + 1) * stride

            for x in xrange(x_min, x_max, stride):
                for y in xrange(y_min, y_max, stride):
                    yield self._pyramid.create_metatile_index(z, x, y, stride)


class TileListPyramidWalker(object):

    def __init__(self, pyramid, tilelist_file,
                 levels=None, stride=1, envelope=None):
        self._tilelist_file = tilelist_file
        self._pyramid = pyramid
        if levels is not None:
            self._levels = levels
        else:
            self._levels = pyramid.levels
        if envelope is not None:
            self._envelope = Envelope.from_tuple(envelope)
        else:
            self._envelope = pyramid.envleope
        self._stride = stride
        assert pyramid.projection == 'EPSG:3857'
        self._proj = GoogleMercatorProjection()

    def walk(self):
        stride = self._stride
        stride_diff = len(bin(stride)) - 3

        with open(self._tilelist_file, 'rb') as fp:

            reader = csv.reader(fp)
            for row in reader:
                tile_z, tile_x, tile_y = tuple(map(int, row))
                for z in self._levels:
                    z_diff = z - tile_z
                    if z_diff < stride_diff:
                        # Skip this level if its smaller than min allowed layer
                        continue
                    for x in xrange(tile_x * (2 ** z_diff), (tile_x + 1) * (2 ** z_diff), stride):
                        for y in xrange(tile_y * (2 ** z_diff), (tile_y + 1) * (2 ** z_diff), stride):
                            yield self._pyramid.create_metatile_index(z, x, y, stride)
