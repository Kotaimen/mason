'''
Created on Apr 29, 2012

@author: Kotaimen
'''


class TileIndex(object):

    def __init__(self, z, x, y):
        pass





class TileData(object):

    def __init__(self):
        self._data = None

    @property
    def data(self):
        return self._data

class TileMetadata(object):
    pass


class Tile(object):

    def __init__(self, index, data, metadata):
        pass

