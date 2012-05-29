'''
Created on May 26, 2012

@author: ray
'''

import mimetypes


#==============================================================================
# Data Type
#==============================================================================
class DataType(object):

    """ Data Type

    name
        name of data type
    ext
        file extension of data type
    parameter
        parameter, (eg. quality, transparency)
    """

    def __init__(self, name, ext, parameters=None):
        self._name = name
        self._parameters = parameters

        self._ext = ext

        # mimetypes.guess_type() gives different result on '.png' and
        # '.jpg' on Python2.7 and Python3.2, while types_map returns
        # the same.
        self._mimetype = mimetypes.types_map[ext]

    @property
    def name(self):
        return self._name

    @property
    def parameters(self):
        return self._parameters

    @property
    def ext(self):
        return self._ext

    @property
    def mimetype(self):
        return self._mimetype


#==============================================================================
# Various Data Types
#==============================================================================
class PNGDataType(DataType):

    """ PNG Data Type """

    def __init__(self, parameters=None):
        DataType.__init__(self, 'png', '.png', parameters)


class PNG256DataType(DataType):

    """ PNG256 Data Type """

    def __init__(self, parameters=None):
        DataType.__init__(self, 'png256', '.png', parameters)


class GTIFFDataType(DataType):

    """ GTIFF Data Type """

    def __init__(self, parameters=None):
        DataType.__init__(self, 'gtiff', '.tif', parameters)


class JPEGDataType(DataType):

    """ JPEG Data Type """

    def __init__(self, parameters=None):
        DataType.__init__(self, 'jpeg', '.jpg', parameters)


#==============================================================================
# Render Data
#==============================================================================
class RenderData(object):

    """ Wrapper of Rendering data

    A RenderData wraps the raw tile data with its data type.

    data
        raw tile data, some binary stream

    data_type
        data type of the raw data

    """

    def __init__(self, data, data_type):
        assert isinstance(data_type, DataType)
        self._data = data
        self._data_type = data_type

    @property
    def data(self):
        return self._data

    @property
    def data_type(self):
        return self._data_type


#==============================================================================
# Render Data Factory
#==============================================================================
class DataTypeFactory(object):

    """ Data Type Factory """

    DATATYPE_CLASS = dict(png=PNGDataType,
                          png256=PNG256DataType,
                          gtiff=GTIFFDataType,
                          jpeg=JPEGDataType
                          )

    def __call__(self, name, parameters=None):
        try:
            data_class = self.DATATYPE_CLASS[name]
        except KeyError:
            raise Exception('Unknown data type "%s"' % name)

        return data_class(parameters)


def create_data_type(name, parameters=None):

    """ Create Function """

    return DataTypeFactory()(name, parameters)
