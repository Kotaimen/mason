# -*- coding:utf-8 -*-
'''
MetaTile Composer

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

    def __init__(self, command):
        self._command = command

    def compose(self, metatile_list):
        assert all(isinstance(m, MetaTile) for m in metatile_list)
        index = metatile_list[0].index
        data = ''
        fmt = Format.ANY
        mtime = time.time()
        metatile = MetaTile.from_tile_index(index, data, fmt, mtime)
        return metatile
