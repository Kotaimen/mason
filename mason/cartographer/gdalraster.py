# -*- coding:utf-8 -*-
'''
Created on Sep 1, 2012

@author: ray
'''
import os
from ..utils import adhoc
from ..core.format import Format


class GDALRaster(object):

    def __init__(self, data=None, data_format=None):
        self._data = data
        self._data_format = data_format

    @property
    def data(self):
        return self._data

    @property
    def data_format(self):
        return self._data_format


class GDALTempFileRaster(GDALRaster):

    def __init__(self, data_format=Format.ANY):
        GDALRaster.__init__(self, data_format=data_format)
        self._filename = adhoc.create_temp_filename(os.getpid())

    @property
    def filename(self):
        return self._filename

    def load(self):
        with open(self._filename, 'rb') as fp:
            self._data = fp.read()

    def save(self, data):
        with open(self._filename, 'wb') as fp:
            fp.write(data)

    def close(self):
        if os.path.exists(self._filename):
            os.remove(self._filename)
