""" Data format management

Format is just a simple metadata dictionary.

A namespace class `Format` is provided to easily access known formats and
do attributes checks and validations

Created on Aug 28, 2012
@author: Kotaimen
"""

KNOWN_FORMATS = {
    'ANY': dict(name='ANY',
                driver='',
                type='',
                extension='',
                mimetype='',
                georeferenced='no',
                ),

    'PNG': dict(name='PNG',
                driver='Portable Network Graphics, RGBA',
                type='raster',
                extension='.png',
                mimetype='image/png',
                georeferenced='no',
                ),

    'PNG256': dict(name='PNG256',
                driver='Portable Network Graphics, indexed',
                type='raster',
                extension='.png',
                mimetype='image/png',
                georeferenced='no',
                ),

    'JPG': dict(name='JPG',
                driver='JPEG',
                type='raster',
                extension='.jpg',
                mimetype='image/jpeg',
                georeferenced='no',
                ),

    'GTIFF': dict(name='GTIFF',
                driver='Geo TIFF',
                type='raster',
                extension='.tif',
                mimetype='image/tiff',
                georeferenced='yes',
                ),

    'TIFF': dict(name='TIFF',
                driver='TIFF',
                type='raster',
                extension='.tif',
                mimetype='image/tiff',
                georeferenced='no',
                ),
}


class Format(object):

    @staticmethod
    def get_known_formats():
        return KNOWN_FORMATS.keys()

    @staticmethod
    def is_known_format(fmt):
        for known_fmt in KNOWN_FORMATS.itervalues():
            if fmt == known_fmt:
                return True
        else:
            return False

    @staticmethod
    def is_raster(fmt):
        return fmt['type'] == 'raster'

    @staticmethod
    def is_georeferenced(fmt):
        return fmt['georeferenced'] == 'yes'


for k, v in KNOWN_FORMATS.iteritems():
    setattr(Format, k, v)
#Format..update(KNOWN_FORMATS)
