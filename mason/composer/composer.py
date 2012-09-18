# -*- coding:utf-8 -*-
'''
Base class of Image Composer

Created on May 18, 2012
@author: ray
'''


#==============================================================================
# Base Class of Tile Composer
#==============================================================================
class ImageComposer(object):

    """ Compose tiles using image processing engine """

    def __init__(self, format='ANY'):
        self._format = format

    @property
    def output_format(self):
        return self._format

    def compose(self, image_list):
        """ composes a list of tiles to one tile """
        raise NotImplementedError
