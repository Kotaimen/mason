'''
Created on May 26, 2012

@author: ray
'''

import mimetypes


#==============================================================================
# Tile Data
#==============================================================================
class TileData(object):

    """ Tile Data Wrapper

    A TileData wraps the raw tile data with its data type, extension,
    mime-type, and data parameters.

    data
        raw tile data, some binary stream

    data_type
        data type of the raw data

    ext
        file extension of the data type

    data_parameters
        parameters of the data, (eg: quality for jpeg, palette for png256)

    """

    def __init__(self, data, data_type, ext, data_parameters=dict()):
        self._data = data
        self._data_type = data_type
        self._data_parameters = data_parameters

        self._ext = ext

        # mimetypes.guess_type() gives different result on '.png' and
        # '.jpg' on Python2.7 and Python3.2, while types_map returns
        # the same.
        self._mimetype = mimetypes.types_map[ext]

    @property
    def data(self):
        return self._data

    @property
    def data_type(self):
        return self._data_type

    @property
    def data_parameter(self):
        return self._data_parameters

    @property
    def ext(self):
        return self._ext

    @property
    def mimetype(self):
        return self._mimetype


#==============================================================================
# Various Types of Tile Data
#==============================================================================
class PNGTileData(TileData):

    """ PNG Tile Data

    True-Color PNG Data
    """

    def __init__(self, data, data_parameters=dict()):
        TileData.__init__(self, data, 'png', '.png', data_parameters)


class PNG256TileData(TileData):

    """ PNG256 Tile Data

    PNG Data with index color
    """

    def __init__(self, data, data_parameters=dict()):
        TileData.__init__(self, data, 'png256', '.png', data_parameters)


class GTIFFData(TileData):

    """ GTIFF Tile Data

    TIFF with GEO Information
    """

    def __init__(self, data, data_parameters=dict()):
        TileData.__init__(self, data, 'gtiff', '.tif', data_parameters)


class JPEGData(TileData):

    """ JPEG Tile Data """

    def __init__(self, data, data_parameters=dict()):
        TileData.__init__(self, data, 'jpeg', '.jpg', data_parameters)


class TileDataFactory(object):

    """ Tile Data Factory """

    DATATYPE_CLASS = dict(png=PNGTileData,
                          png256=PNG256TileData,
                          gtiff=GTIFFData,
                          jpeg=JPEGData)

    def __call__(self, data_type, data, data_parameters=dict()):
        try:
            data_class = self.DATATYPE_CLASS[data_type]
        except KeyError:
            raise Exception('Unknown data type "%s"' % data_type)

        return data_class(data, data_parameters)


def create_tile_data(data_type, data, data_parameters=dict()):

    """ Create Function """

    return TileDataFactory()(data_type, data, data_parameters)
