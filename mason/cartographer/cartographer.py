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
    def __init__(self, data_type):
        assert data_type is not None
        self._data_type = data_type

    def doodle(self, envelope=(-180, -90, 180, 90), size=(256, 256)):
        """ Make geographic data in the envelope and project to
        Google Mercator.

        envelope
            a tuple of left-bottom and right-top lonlat in WGS84
        size
            output map size if necessary
        """
        raise NotImplementedError

    def close(self):
        pass


#==============================================================================
# Derived Types of Cartographer
#==============================================================================
class Raster(Cartographer):

    """ Raster Cartographer """

    pass


class GeoJson(Cartographer):

    """ GEO JSON Cartographer """

    pass
