'''
Created on May 2, 2012

@author: ray
'''

import os
# from mapnik 2.0.1, module name mapnik2 is deprecated.
# using mapnik instead.
import mapnik
from .cartographer import Raster, Vector
from .errors import (MapnikVersionError,
                     MapnikThemeNotFound,
                     MapnikTypeError)

MAPNIK_AGG_RENDERER = True
MAPNIK_CAIRO_RENDERER = mapnik.has_cairo()
MAPNIK_HAS_JPEG = mapnik.has_jpeg()
MAPNIK_VERSION = mapnik.mapnik_version() / 100000

if MAPNIK_VERSION < 2:
    raise MapnikVersionError('Only Mapnik 2.0.0 and later is supported')

try:
    # XXX: We hack the code of mapnik and enables a svg output.
    MPANIK_HAS_SVG = mapnik.has_svg()
except AttributeError:
    MPANIK_HAS_SVG = False


# google mercator projection. alias to 'EPSG:900913'
_PROJECTIONS = {
'EPSG:3857': '+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 ' \
             '+y_0=0 +units=m +k=1.0 +nadgrids=@null +over +no_defs',
}



#===============================================================================
# Raster Maker in Mapnik
#===============================================================================
class MapnikRaster(Raster):

    def __init__(self,
                 theme_root,
                 theme_name,
                 scale_factor=1.0,
                 buffer_size=0,
                 image_type='png',
                 image_parameters=None,
                 ):
        Raster.__init__(self, image_type, image_parameters)

        self._scale_factor = scale_factor
        self._buffer_size = buffer_size

        # check theme path
        self._theme = os.path.abspath(os.path.join(theme_root, '%s.xml' % theme_name))
        if not os.path.exists(self._theme):
            raise MapnikThemeNotFound(self._theme)

        # 'png', 'png24', 'png32' are equivalent to 'png32' in mapnik
        # 'png8', 'png256' are equivalent to 'png256' in mapnik
        if image_type not in ['png', 'png256']:
            raise MapnikTypeError('Image Type %s not supported' % image_type)

        # convert image_type and parameters to mapnik format string
        if image_parameters:
            if 'colors' in image_parameters:
                if image_type == 'png':
                    raise MapnikTypeError('Only indexed image support colors')
                colors = image_parameters['colors']
                if colors < 2 or colors > 256:
                    raise MapnikTypeError('Invalid color numbers')
                self._image_type += (':c=%d' % colors)

            if 'transparency' in image_parameters:
                transparency = image_parameters['transparency']
                self._image_type += (':t=%d' % (1 if transparency else 0))

        # lazy initialize map object
        self._map = None
        self._map_size = None

        # projection
        self._proj = mapnik.Projection(_PROJECTIONS['EPSG:3857'])


    def make(self, envelop=(-180, -85, 180, 85), size=(256, 256)):

        if self._map_size != size or self._map is None:
            self._map_size = size
            mapnik.load_map(self._map, self._theme)

        map_ = self._map
        map_.buffer_size = self._buffer_size

        bbox = mapnik.Box2d(*envelop)
        bbox = self._proj.forward(bbox)

        map_.zoom_to_box(bbox)

        image = mapnik.Image(*size)
        mapnik.render(map_, image, self._scale_factor)
        return image.tostring(self._image_type)


#===============================================================================
# Vector Maker of Mapnik 
#===============================================================================
class MapnikVector(Vector):

    def __init__(self,
                 theme_root,
                 theme_name,
                 buffer_size=0,
                 vector_type='svg',
                 vector_parameters=None,
                 ):
        Vector.__init__(self, vector_type, vector_parameters)

        self._buffer_size = buffer_size

        # check theme path
        self._theme = os.path.abspath(os.path.join(theme_root, '%s.xml' % theme_name))
        if not os.path.exists(self._theme):
            raise MapnikThemeNotFound(self._theme)

        # lazy initialize map object
        self._map = None
        self._map_size = None

        # projection
        self._proj = mapnik.Projection(_PROJECTIONS['EPSG:3857'])


    def make(self, envelop=(-180, -85, 180, 85), size=(256, 256)):

        if self._map_size != size or self._map is None:
            self._map = mapnik.Map(*size)
            mapnik.load_map(self._map, self._theme)

        map_ = self._map
        map_.buffer_size = self._buffer_size

        bbox = mapnik.Box2d(*envelop)
        bbox = self._proj.forward(bbox)

        map_.zoom_to_box(bbox)

        # XXX:Use custom built svg renderer
        if MPANIK_HAS_SVG and self._vector_type == 'svg':
            return mapnik.render_svg(map_)
        else:
            raise MapnikTypeError('Vector type %s is not supported' % self._vector_type)
