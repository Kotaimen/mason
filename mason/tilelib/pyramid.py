'''
Created on Apr 29, 2012

@author: Kotaimen
'''

from .tile import TileIndex, Tile

#===============================================================================
# Exceptions
#===============================================================================

class TileOutOfEnvelope(Exception):
    pass

class InvalidTileLayer(Exception):
    pass

class Pyramid(object):

    """ Represents a quad-tree structure of tile Pyramid

    Hides geography calculations behind this class.  Also being a factory of
    TileIndex object.
    """

    def __init__(self,
                 levels=range(0, 11),
                 tile_size=256,
                 envelope=(-180, -85.06, 180, 85.06),
                 crs='ESPG:4326',
                 proj='ESPG:909913',
                 ):
        """
        Create a new Pyramid object, arguments:

        level
            Tile levels, a list of integers, note levels is not necessary
            continuous.

        tile_size
            Pixel size of a tile in the Pyramid, always a multiple of 256.

        envelope
            Envelope of valid tile range in (left, bottom, right, top) tuple.
            Tiles outside this envelope cannot be created.

        crs
            Authority ID of geography coordinate reference system, default is
            EPSG:4326

        proj
            Authority ID of map projection

        """
        assert levels
        assert (tile_size % 256) == 0
        # Only supports WGS84 lonlat to GoogleMecartor projection
        assert crs == 'ESPG:4326' and proj == 'ESPG:909913'
        self._levels = levels
        self._tile_size = tile_size
        self._envelope = envelope
        self._crs = crs
        self._proj = proj

    @property
    def levels(self):
        return self._levels

    @property
    def tile_size(self):
        return self._tile_size

    @property
    def envelope(self):
        return self._envelope

    @property
    pass

