"""
Iterate over a Pyramid and generate TileIndexes

Created on Aug 31, 2012
@author: Kotaimen
"""

from .geo import SRID, Envelope


class PyramidWalker(object):

    def __init__(self, pyramid, levels=None, stride=1, envelope=None):
        self._pyramid = pyramid
        if levels is not None:
            self._levels = levels
        else:
            self._levels = pyramid.levels
        if envelope is not None:
            minx, miny, maxx, maxxy = envelope
            srid = SRID('epsg', 4326)
            evelope = (minx, miny, maxx, maxxy, srid)
            self._envelope = Envelope.from_tuple(evelope)
        else:
            self._envelope = pyramid.envleope
        self._stride = stride
        assert pyramid.projection == 'EPSG:3857'

    def walk(self):
        stride = self._stride
        for z in self._levels:
            lt_x, lt_y = self._envelope.lefttop
            rb_x, rb_y = self._envelope.rightbottom\

            left, top = self._pyramid.coords_wgs842xyz(z, lt_x, lt_y)
            right, bottom = self._pyramid.coords_wgs842xyz(z, rb_x, rb_y)

#            left, top = self._proj.coord2tile(self._envelope.lefttop, z)
#            right, bottom = self._proj.coord2tile(self._envelope.rightbottom, z)

            x_min = left // stride * stride
            y_min = top // stride * stride

            x_max = ((right // stride) + 1) * stride
            y_max = ((bottom // stride) + 1) * stride

            for x in xrange(x_min, x_max, stride):
                for y in xrange(y_min, y_max, stride):
                    yield self._pyramid.create_metatile_index(z, x, y, stride)


class ShapefilePyramidWalker(object):

    pass

