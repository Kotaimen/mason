'''
Created on May 18, 2012

@author: ray
'''


#==============================================================================
# Errors
#==============================================================================
class TileComposerError(object):
    pass


#==============================================================================
# Base Class of Tile Composer
#==============================================================================
class TileComposer(object):

    """ Compose a list of tiles """

    def __init__(self, tag, data_type):
        self._tag = tag
        self._data_type = data_type

    @property
    def tag(self):
        """ composer tag """
        return self._tag

    @property
    def data_type(self):
        """ data_type of composer result """
        return self._data_type

    def compose(self, tiles):
        """ composes a list of tiles to one tile """
        raise NotImplementedError

