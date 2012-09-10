# -*- coding:utf-8 -*-
'''
MetaTile DataSource

Created on Sep 9, 2012
@author: ray
'''
import time
from ..core import MetaTile


#==============================================================================
# Base Class of MetaTile DataSource
#==============================================================================
class MetaTileDataSource(object):

    def get(self, metatileindex):
        raise NotImplementedError


class CartographerMetaTileDataSource(MetaTileDataSource):

    """ Cartographer DataSource

    A DataSource wrapper for cartographer
    """

    def __init__(self, cartographer):
        self._cartographer = cartographer

    def get(self, metatileindex):
        envelope = metatileindex.envelope
        size = metatileindex.tile_size

        data_stream = self._cartographer.render(envelope, size)
        data_format = self._cartographer.output_format
        mtime = time.time()

        metatile = MetaTile.from_tile_index(data_stream, data_format, mtime)
        return metatile
