# -*- coding:utf-8 -*-
'''
Created on Sep 9, 2012

@author: ray
'''
import time
from ..core import MetaTile

from .base import MetaTileRenderer


#==============================================================================
# MetaTile renderer
#==============================================================================
class NullMetaTileRenderer(MetaTileRenderer):

    """ Null renderer

    A renderer always return None.
    """

    def render(self, metatileindex):
        return None


class CartographerMetaTileRenderer(MetaTileRenderer):

    """ Cartographer renderer

    A renderer uses cartographer as its source.
    """

    def __init__(self, cartographer):
        self._cartographer = cartographer

    def render(self, metatileindex):
        envelope = metatileindex.envelope
        size = metatileindex.tile_size

        data_stream = self._cartographer.render(envelope, size)
        data_format = self._cartographer.output_format
        mtime = time.time()

        metatile = MetaTile.from_tile_index(data_stream, data_format, mtime)
        return metatile
