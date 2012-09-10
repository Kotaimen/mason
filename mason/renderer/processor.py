# -*- coding:utf-8 -*-
'''
MetaTile Processor

Created on Sep 10, 2012
@author: ray
'''
import time
from ..core import MetaTile
from ..cartographer import GDALRaster


#==============================================================================
# Base class of MetaTile Processor
#==============================================================================
class MetaTileProcessor(object):

    def process(self, metatile):
        raise NotImplementedError


class GDALMetaTileProcessor(MetaTileProcessor):

    def __init__(self, gdal_processor):
        self._processor = gdal_processor

    def process(self, metatile):
        data = metatile.data
        data_format = metatile.format

        raster = GDALRaster(data, data_format.name)
        raster_processed = self._processor.convert(raster)
        mtime = time.time()

        metatile = MetaTile.from_tile_index(metatile.index,
                                            raster_processed.data,
                                            raster_processed.data_format,
                                            mtime)

        return metatile
