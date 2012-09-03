# -*- coding:utf-8 -*-
'''
GDAL Raster Wrappers

Created on Sep 1, 2012
@author: ray
'''
import os
from ..core import Format
from ..utils import adhoc


class GDALRaster(object):

    """ A wrapper of raster object

    GDAL processor accept GDALRaster as both input and output.

    data:
        raster data

    data_format:
        format of raster data. default, Format.ANY.

    """

    def __init__(self, data=None, data_format=Format.ANY):
        """ create a raster object """
        self._data = data
        self._data_format = data_format

    @property
    def data(self):
        """ return raster data """
        return self._data

    @property
    def data_format(self):
        """ return raster format """
        return self._data_format


class GDALTempFileRaster(GDALRaster):

    """ A wrapper for temporary raster object

    GDAL processor takes only on-disk files as input and output.
    As a result, input data should be put into a temporary file before
    being further processed and output data should be read from the
    assigned temporary file.

    data_format:
        format of raster data. default, Format.ANY.

    prefix:
        prefix of the temporary file

    suffix:
        suffix of the temporary file

    """

    def __init__(self,
                 data_format=Format.ANY,
                 prefix='',
                 suffix=str(os.getpid())):
        """ create a temporary raster file """
        GDALRaster.__init__(self, data_format=data_format)
        self._filename = adhoc.create_temp_filename(prefix, suffix)

    @property
    def filename(self):
        """ return temporary filename """
        return self._filename

    def load(self):
        """ load data from file """
        with open(self._filename, 'rb') as fp:
            self._data = fp.read()

    def save(self, data):
        """ save data to file"""
        with open(self._filename, 'wb') as fp:
            fp.write(data)

    def close(self):
        """ remove temporary file """
        if os.path.exists(self._filename):
            os.remove(self._filename)
