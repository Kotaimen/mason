# -*- coding:utf-8 -*-
'''
ImageMagick Composer

Created on Sep 10, 2012
@author: ray
'''
import time
from ..core import MetaTile, Format


#==============================================================================
# Base class of MetaTile Composer
#==============================================================================
class MetaTileComposer(object):

    def compose(self, metatile_list):
        raise NotImplementedError


class ImageMagicMetaTileComposer(MetaTileComposer):

    def __init__(self, composer):
        self._composer = composer

    def compose(self, metatile_list):
        assert all(isinstance(m, MetaTile) for m in metatile_list)
        index = metatile_list[0].index

        image_list = list((m.data, m.format.extension) for m in metatile_list)

        data_stream = self._composer.compose(image_list)
        try:
            data_format = Format.from_name(self._composer.output_format)
            mtime = time.time()

            metatile = MetaTile.from_tile_index(index,
                                                data_stream.getvalue(),
                                                data_format,
                                                mtime)
        finally:
            data_stream.close()
        return metatile
