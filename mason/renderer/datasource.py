# -*- coding:utf-8 -*-
'''
MetaTile DataSource

Created on Sep 9, 2012
@author: ray
'''
import time
from ..core import MetaTile, Format


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
        envelope = metatileindex.buffered_envelope.make_tuple()
        tile_size = metatileindex.buffered_tile_size
        size = (tile_size, tile_size)
        data_stream = self._cartographer.render(envelope, size)
        try:
            data_format = Format.from_name(self._cartographer.output_format)
            mtime = time.time()
            metatile = MetaTile.from_tile_index(metatileindex,
                                                data_stream.getvalue(),
                                                data_format,
                                                mtime)
        finally:
            data_stream.close()

        return metatile


class StorageMetaTileDataSource(MetaTileDataSource):

    def __init__(self, storage):
        self._storage = storage

    def get(self, metatileindex):
        metatile = self._storage.get(metatileindex)
        return metatile
