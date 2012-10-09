""" Data format management

Format is just a simple metadata dictionary.

A namespace class `Format` is provided to easily access known formats and
do attributes checks and validations

Created on Aug 28, 2012
@author: Kotaimen
"""

import collections


class _Format(collections.namedtuple('_Format',
                                     '''name driver type extension
                                        mimetype georeferenced''')):
    def make_dict(self):
        return self._asdict()

KNOWN_FORMATS = {
    'ANY': _Format(name='ANY',
                   driver='',
                   type='',
                   extension='',
                   mimetype='',
                   georeferenced='no',
                   ),

    'DATA': _Format(name='DATA',
                    driver='Any binary data',
                    type='binary',
                    extension='.dat',
                    mimetype='application/data',
                    georeferenced='no',
                    ),

    'GEOJSON': _Format(name='GEOJSON',
                    driver='Any binary data',
                    type='text',
                    extension='.json',
                    mimetype='application/json',
                    georeferenced='yes',
                    ),

    'PNG': _Format(name='PNG',
                   driver='Portable Network Graphics, RGBA',
                   type='raster',
                   extension='.png',
                   mimetype='image/png',
                   georeferenced='no',
                   ),

    'PNG256': _Format(name='PNG256',
                      driver='Portable Network Graphics, indexed',
                      type='raster',
                      extension='.png',
                      mimetype='image/png',
                      georeferenced='no',
                      ),

    'JPG': _Format(name='JPG',
                   driver='JPEG',
                   type='raster',
                   extension='.jpg',
                   mimetype='image/jpeg',
                   georeferenced='no',
                   ),
#
#    'JPEG': _Format(name='JPG',
#                   driver='JPEG',
#                   type='raster',
#                   extension='.jpg',
#                   mimetype='image/jpeg',
#                   georeferenced='no',
#                   ),

    'GTIFF': _Format(name='GTIFF',
                     driver='Geo TIFF',
                     type='raster',
                     extension='.tif',
                     mimetype='image/tiff',
                     georeferenced='yes',
                     ),

    'TIFF': _Format(name='TIFF',
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
        assert isinstance(fmt, _Format)
        for known_fmt in KNOWN_FORMATS.itervalues():
            if fmt == known_fmt:
                return True
        else:
            return False

    @staticmethod
    def is_raster(fmt):
        return fmt.type == 'raster'

    @staticmethod
    def is_georeferenced(fmt):
        return fmt.georeferenced == 'yes'

    @staticmethod
    def from_dict(mapping):
        return _Format(**mapping)

    @staticmethod
    def from_name(name):
        return KNOWN_FORMATS[name.upper()]

    @staticmethod
    def from_extension(extension):
        for fmt in KNOWN_FORMATS.itervalues():
            if fmt.extension == extension:
                return fmt
        else:
            raise KeyError(extension)

# Inject formats into class so can use them like Enum
for k, v in KNOWN_FORMATS.iteritems():
    setattr(Format, k, v)

