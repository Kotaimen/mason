'''
Created on May 2, 2012

@author: ray
'''

import os
import io
import sys
import threading

from ..core import Format
from .cartographer import Cartographer

try:
    # From mapnik 2.0.1, module name mapnik2 is deprecated
    import mapnik
except ImportError:
    # In case of mapnik 2.0.0 or 0.7.x
    import mapnik2 as mapnik

MAPNIK_VERSION = mapnik.mapnik_version() / 100000

# Automatically add system font directory
if sys.platform == 'darwin':
    mapnik.register_fonts(r'/Library/Fonts/')
elif sys.platform == 'linux':
    mapnik.register_fonts(r'/usr/share/fonts')
elif sys.platform == 'win32':
    mapnik.register_fonts(r'C:\Windows\Fonts')

#for face in list(mapnik.FontEngine.face_names()):
#    print face


#==============================================================================
# Render maps using mapnik
#==============================================================================
class Mapnik(Cartographer):

    """ Mapnik Renderer

    Mapnik is a Free Toolkit for developing mapping applications.
    It is written in modern C++ and has Python bindings that support
    fast-paced agile development.

    Mapnik takes a theme xml file, which defines data source
    and style for rendering, as its input and output a map data of
    a specified output format.

    theme
        Pathname of the mapnik xml configuration file

    projection
        Map projection specfied in 'EPSG:XXXX', default is EPSG:3857

    scale_factor
        Used to scale font/symbol/thickness, useful when scaling

    buffer_size
        Data around the specified area will be rendered to enhance
        connectivity between continuous area(tile).

    image_type
        output format, PNG, PNG256, JPEG is supported now.

    image_parameters
        PNG:
            None

        JPEG:
            Key: 'quality'
            Val: 1-100 jpeg quality.

        PNG256:
            Key: 'palette'
            Val: A file path to a palette file. A palette file format can be:
                    a buffer with RGBA values (4 bytes),
                    a buffer with RGB values (3 bytes),
                    an Adobe Photoshop .act file.

            Key: 'colors'
            Val: Number of colors to use.
                 If 'palette' is specified, this option will take no effect.

            Key: 'transparency'
            Val: Mapnik transparency mode:
                    0-no alpha,
                    1-binary alpha(0 or 255),
                    2-full alpha range

    """

    def __init__(self,
                 theme='map.xml',
                 projection='EPSG:3857',
                 scale_factor=1.0,
                 buffer_size=0,
                 image_type='png',
                 image_parameters=None,
                 ):
        if image_type not in ['png', 'png256', 'jpeg']:
            raise TypeError('Only support PNG/PNG256/JPEG format.')

        self._scale_factor = scale_factor
        self._buffer_size = buffer_size
        self._palette = None

        # check theme path
        self._theme = theme
        if not os.path.exists(self._theme):
            raise Exception('Theme %s not found.' % self._theme)

        Cartographer.__init__(self, image_type.upper())

        # convert image_type and parameter to mapnik format string
        self._image_type = self._init_image_type(image_type, image_parameters)
        self._proj = None
        self._map = self._init_mapnik(projection)

    def _init_image_type(self, image_type, image_parameters):

        if image_parameters:
            # PNG Parameters --------------------------------------------------
            if image_type == 'png':
                image_type += ''
            elif image_type == 'jpeg': # quality
                quality = image_parameters.get('quality', None)
                if not isinstance(quality, int):
                    raise ValueError('JPEG quality shall be an integer.')
                if quality < 1 or quality > 100:
                    raise ValueError('JPEG quality shall be 1-100.')
                # no need to set quality 85, since it is the default value.
                if quality != 85:
                    image_type += '%d' % quality
            # PNG256 Parameters -----------------------------------------------
            elif image_type == 'png256': # palette
                palette = image_parameters.get('palette', None)
                if palette:
                    palette_type = os.path.splitext(palette)[1][1:].lower()
                    if palette_type not in ['rgba', 'rgb', 'act']:
                        raise ValueError('Palette file should have suffix'
                            'rgba/rgb/act to indicate its type')
                    with open(palette, 'rb') as fp:
                        palette_data = fp.read()
                    self._palette = mapnik.Palette(palette_data, palette_type)
                else:
                    colors = image_parameters.get('colors', None)
                    if colors:
                        if colors < 2 or colors > 256:
                            raise ValueError('Invalid color numbers')
                        image_type += ':c=%d' % colors
                # transparency
                # colors, if palette is specified, colors will take no effect.
                transparency = image_parameters.get('transparency', None)
                if transparency in [0, 1, 2]:
                    image_type += ':t=%d' % transparency
                    # JPEG Parameters -------------------------------------------------

        return image_type

    def _init_mapnik(self, projection):
        projection = '+init=%s' % projection.lower()
        mapper = mapnik.Map(1, 1, projection)
        mapnik.load_map(mapper, self._theme)
        self._proj = mapnik.Projection(projection)
        mapper.buffer_size = self._buffer_size
        return mapper

    def render(self, envelope=(-180, -85, 180, 85), size=(256, 256)):
        bbox = mapnik.Box2d(*envelope)

        bbox = self._proj.forward(bbox)
        self._map.resize(*size)
        self._map.zoom_to_box(bbox)

        image = mapnik.Image(*size)
        mapnik.render(self._map, image, self._scale_factor)

        if self._palette:
            data = image.tostring(self._image_type, self._palette)
        else:
            data = image.tostring(self._image_type)

        return io.BytesIO(data)


