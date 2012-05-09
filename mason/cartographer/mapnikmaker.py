'''
Created on May 2, 2012

@author: ray
'''

import os
# from mapnik 2.0.1, module name mapnik2 is deprecated.
# using mapnik instead.
import mapnik
from .cartographer import Raster
from .errors import (MapnikVersionError,
                     MapnikThemeNotFound,
                     MapnikTypeError,
                     MapnikParamError)

MAPNIK_AGG_RENDERER = True
MAPNIK_CAIRO_RENDERER = mapnik.has_cairo()
MAPNIK_HAS_JPEG = mapnik.has_jpeg()
MAPNIK_VERSION = mapnik.mapnik_version() / 100000

if MAPNIK_VERSION < 2:
    raise MapnikVersionError('Only Mapnik 2.0.0 and later is supported')


# Google mercator projection. alias to 'EPSG:3857'
_PROJECTIONS = {
'EPSG:3857': '+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 ' \
             '+x_0=0.0 +y_0=0 +units=m +k=1.0 +nadgrids=@null +over +no_defs',
}


#==============================================================================
# Raster Maker in Mapnik
#==============================================================================
class MapnikRaster(Raster):

    """ Mapnik Raster Renderer

    Mapnik is a Free Toolkit for developing mapping applications.
    It is written in modern C++ and has Python bindings that support
    fast-paced agile development.

    Mapnik takes a theme xml file, which defines data source
    and style for rendering, as its input and output a map data of
    a specified output format.


    theme_root
        Root directory of Mapnik theme.

    theme_name
        File name of theme (without xml extension).

    scale_factor
        Used to increase or decrease font and symbol sizes,
        line widths, and dash-array spacing.

    buffer_size
        Data around the specified area will be rendered to enhance
        connectivity between continuous area(tile).

    image_type
        output format, PNG is supported now.

    image_parameters
        palette
            A file path to a palette file. A palette file format can be
            a buffer with RGBA values (4 bytes),
            a buffer with RGB values (3 bytes),
            an Adobe Photoshop .act file.

        color
            Number of colors to use a index image.
            If palette is specified, this option will take no effect.

        transparency
            A float to represent the transparency of the image.

    """

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
        self._palette = None

        # check theme path
        self._theme = os.path.abspath(os.path.join(theme_root,
                                                   '%s.xml' % theme_name))
        if not os.path.exists(self._theme):
            raise MapnikThemeNotFound(self._theme)

        # 'png', 'png24', 'png32' are equivalent to 'png32' in mapnik
        # 'png8', 'png256' are equivalent to 'png256' in mapnik
        if image_type not in ['png', 'png256']:
            raise MapnikTypeError('Image Type %s not supported' % image_type)

        # convert image_type and parameters to mapnik format string
        if image_parameters:
            if 'palette' in image_parameters:
                palette_file = image_parameters['palette']
                if self._palette and not os.path.exists(self._palette):
                    raise MapnikParamError('Palette File does not exists.')
                if self._image_type == 'png':
                    raise MapnikTypeError('Only indexed image support colors')

                palette_type = os.path.splitext(palette_file)[1][1:].lower()
                if palette_type not in ['rgba', 'rgb', 'act']:
                    raise MapnikTypeError('Palette file should have ' \
                                          'rgba/rgb/act to indicate its type')

                with open(palette_file, 'rb') as fp:
                    palette_data = fp.read()
                self._palette = mapnik.Palette(palette_data, palette_type)

            # index color option will take effect if palette does not exists.
            if not self._palette and 'colors' in image_parameters:
                if image_type == 'png':
                    raise MapnikTypeError('Only indexed image support colors')
                colors = image_parameters['colors']
                if colors < 2 or colors > 256:
                    raise MapnikTypeError('Invalid color numbers')
                self._image_type += (':c=%d' % colors)

            if 'transparency' in image_parameters:
                transparency = image_parameters['transparency']
                self._image_type += (':t=%d' % (1 if transparency else 0))

        # projection
        self._proj = mapnik.Projection(_PROJECTIONS['EPSG:3857'])

    def make(self, envelope=(-180, -85, 180, 85), size=(256, 256)):

        map_ = mapnik.Map(*size)
        mapnik.load_map(map_, self._theme)
        map_.buffer_size = self._buffer_size

        bbox = mapnik.Box2d(*envelope)
        bbox = self._proj.forward(bbox)

        map_.zoom_to_box(bbox)

        image = mapnik.Image(*size)
        mapnik.render(map_, image, self._scale_factor)

        if self._palette:
            return image.tostring(self._image_type, self._palette)
        else:
            return image.tostring(self._image_type)
