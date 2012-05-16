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
    @property
    def data_type(self):
        raise NotImplementedError

    def doodle(self, envelope=(-180, -85, 180, 85), size=(256, 256)):
        """ Make geographic data in the envelope and project to
        Google Mercator.

        bbox: a tuple of left-bottom and right-top lonlat in WGS84
        size: output map size if necessary
        """
        raise NotImplementedError

    def close(self):
        pass


#==============================================================================
# Derived Types of Cartographer
#==============================================================================
class Raster(Cartographer):

    """ Raster map maker

    Different Raster Maker support differnt image type.
    Mapnik: png, png256, jpeg
    GDAL: gtiff
    """

    def __init__(self,
                 image_type='png',
                 image_parameters=None,
                 ):
        if not image_parameters:
            image_parameters = dict()

        assert isinstance(image_type, str)
        assert isinstance(image_parameters, dict)

        self._image_type = image_type.lower()
        self._image_parameters = image_parameters

    @property
    def data_type(self):
        return self._image_type


class GeoJson(Cartographer):
    pass
