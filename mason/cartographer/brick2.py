'''
Created on Nov 11, 2013

@author: Kotaimen
'''

import os
import io
import sys

import mapnik

from .cartographer import Cartographer
from .mapniker import Mapnik
from ..utils import Timer, human_size

#===============================================================================
# Speedup by bypassing IIO and imagemagick composing, used by Brick2 themes
#===============================================================================

class _Mapnik(Mapnik):

    def render(self, envelope=(-180, -85, 180, 85), size=(256, 256)):
        if self._force_reload:
            self._map = mapnik.Map(32, 32, self._proj.params())
            mapnik.load_map(self._map, self._theme)
            self._map.buffer_size = self._buffer_size

        bbox = self._fix_envelope(envelope)
        self._map.resize(*size)
        self._map.zoom_to_box(bbox)

        image = mapnik.Image(*size)
        mapnik.render(self._map, image, self._scale_factor)
        return image


class Brick2(Cartographer):

    def __init__(self,
                 theme='theme',
                 projection='EPSG:3857',
                 scale_factor=1.0,
                 buffer_size=0,
                 ):

        Cartographer.__init__(self, 'png')

        theme_names = ['%s_base.xml' % theme,
                       '%s_label_halo.xml' % theme,
                       '%s_label.xml' % theme,
                       '%s_road.xml' % theme, ]
        buffer_sizes = [0, buffer_size, buffer_size, 16]

        def mkmap(theme_name, buffer_size):
            return _Mapnik(theme_name, projection, scale_factor,
                           buffer_size, image_type='png', force_reload=False)

        self._base_map, self._halo_map, self._label_map, self._road_map = \
            tuple(mkmap(theme_name, buffer_size) for (theme_name, buffer_size)
                  in zip(theme_names, buffer_sizes))

    def render(self, envelope=(-180, -85, 180, 85), size=(256, 256)):
        road = self._road_map.render(envelope, size)
        halo = self._halo_map.render(envelope, size)
        label = self._label_map.render(envelope, size)
        base = self._base_map.render(envelope, size)
        road.premultiply()
        halo.premultiply()
        label.premultiply()
        base.premultiply()
        road.composite(halo, mapnik.CompositeOp.src_atop, 0.5)
        road.composite(base, mapnik.CompositeOp.dst_over)
        road.composite(label, mapnik.CompositeOp.src_over)
        road.demultiply()
        data = road.tostring('png8:c=128:m=o:t=0')
        return io.BytesIO(data)
