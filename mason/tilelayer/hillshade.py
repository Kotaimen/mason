'''
Created on Jun 12, 2012

@author: ray
'''
from ..core import create_data_type_from_ext
from ..utils.gdalutil import gdal_hillshade
from .storage import StorageLayer


class HillShadeMaker(object):

    """ Hill Shade Maker """

    def __init__(self, zfactor, scale, azimuth, altitude):
        self._zfactor = zfactor
        self._scale = scale
        self._azimuth = azimuth
        self._altitude = altitude

    def make(self, data, data_type):
        """ Creates hill shade from data """
        if data_type.name != 'gtiff':
            raise Exception('Only Support gtiff')

        data = gdal_hillshade(data,
                              self._zfactor,
                              self._scale,
                              self._azimuth,
                              self._altitude)

        return data


class HillShadeStorageLayer(StorageLayer, HillShadeMaker):

    """ Hill Shade Storage Layer """

    def __init__(self, tag, storage, zfactor, scale, azimuth, altitude):
        StorageLayer.__init__(self, tag, storage)
        HillShadeMaker.__init__(self, zfactor, scale, azimuth, altitude)

    def _process_tile_data(self, tile):

        data = tile.data
        ext = tile.metadata['ext']

        data_type = create_data_type_from_ext(ext)
        data = self.make(data, data_type)

        return data
