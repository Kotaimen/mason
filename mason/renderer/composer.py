# -*- coding:utf-8 -*-
'''
MetaTile Composer

Created on Sep 10, 2012
@author: ray
'''
import time
from ..core import MetaTile


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
        return None
