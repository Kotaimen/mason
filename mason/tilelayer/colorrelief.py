'''
Created on Jun 12, 2012

@author: ray
'''
from ..core import create_data_type_from_ext
from ..utils.gdalutil import gdal_colorrelief
from .storage import StorageLayer


class ColorReliefMaker(object):

    """ Color Relief Maker """

    def __init__(self, color_context):
        self._color_context = color_context

    def make(self, data, data_type):
        """ Creates color relief from data """
        if data_type.name != 'gtiff':
            raise Exception('Only Support gtiff')

        data = gdal_colorrelief(data, self._color_context)
        return data


class ColorReliefStorageLayer(StorageLayer, ColorReliefMaker):

    """ Color Relief Storage Layer """

    def __init__(self, tag, storage, color_context):
        StorageLayer.__init__(self, tag, storage)
        ColorReliefMaker.__init__(self, color_context)

    def _process_tile_data(self, tile):

        data = tile.data
        ext = tile.metadata['ext']

        data_type = create_data_type_from_ext(ext)
        data = self.make(data, data_type)

        return data
