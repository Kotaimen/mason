'''
Created on Apr 30, 2012

@author: ray
'''

from ..core import Format

#==============================================================================
# Cartographer Base Class
#==============================================================================

class Cartographer(object):

    """ Render a map of given area to specified size

    Cartographer takes a bounding box to generate geographic data
    related to that given area.
    """
    def __init__(self, format):
        self._output_format = format

    @property
    def output_format(self):
        return self._output_format

    def render(self, envelope=(-180, -90, 180, 90), size=(256, 256)):
        """ Make geographic data in the envelope and project to
        Google Mercator.

        envelope
            a tuple of left-bottom and right-top lonlat in WGS84
        size
            output map size
        """
        raise NotImplementedError

    def close(self):
        pass

