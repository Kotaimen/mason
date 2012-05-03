'''
Created on Apr 30, 2012

@author: ray
'''


#==============================================================================
# Cartographer Base Class
#==============================================================================
class Cartographer(object):

    """ Base class of map cartographer

    Cartographer takes a bounding box to generate geographic data
    related to that given area.
    """

    def make(self, envelope=(-180, -85, 180, 85), size=(256, 256)):
        """ Make geographic data in the envelope and project to
        Google Mercator.

        bbox: a tuple of left-bottom and right-top lonlat in WGS84
        size: output map size if necessary
        """
        raise NotImplementedError


#==============================================================================
# Derived Types of Cartographer
#==============================================================================
class Raster(Cartographer):

    """ Raster map maker

    Different Raster Maker support differnt image type.
    Mapnik: png, png256
    GDAL: png, tiff
    """

    def __init__(self,
                 image_type='png',
                 image_parameters=None,
                 ):
        self._image_type = image_type
        self._image_parameters = image_parameters


class GeoJson(Cartographer):
    pass
