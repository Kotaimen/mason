'''
Created on May 14, 2012

@author: Kotaimen
'''

import collections
from .core import Format

#===============================================================================
# Layers
#===============================================================================


class StorageLayer(object):

    """ Storage->Layer adapter """

    def __init__(self, storage):
        self._storage = storage
        metadata = dict()
        metadata.update(self._storage.pyramid.summarize())
        metadata.update(self._storage.metadata.make_dict())
        self._metadata = metadata

    @property
    def metadata(self):
        return self._metadata

    def get_tile(self, z, x, y):
        tile_index = self._storage.pyramid.create_tile_index(z, x, y)
        return self._storage.get(tile_index)

    def render_metatile(self, z, x, y, stride):
        # Storage don't support metatile render...
        raise NotImplementedError

    def close(self):
        self._storage.close()


class RendererLayer(object):

    """ RendererRoot->Layer adapter """

    def __init__(self, rendertree):
        self._rendertree = rendertree
        metadata = dict()
        metadata.update(self._rendertree.pyramid.summarize())
        metadata.update(self._rendertree.metadata.make_dict())
        self._metadata = metadata

    @property
    def metadata(self):
        return self._metadata

    def get_tile(self, z, x, y):
        tile_index = self._rendertree.pyramid.create_tile_index(z, x, y)
        return self._rendertree.render_tile(tile_index)

    def render_metatile(self, z, x, y, stride):
        metatile_index = self._rendertree.pyramid.create_metatile_index(z, x, y, stride)
        self._rendertree.render_metatile(metatile_index)

    def close(self):
        self._rendertree.close()


#===============================================================================
# Exceptions
#===============================================================================

class InvalidLayer(Exception):
    pass


class TileNotFound(Exception):
    pass


class Mason(object):

    """ The "TileNamespaceManager", create and manage one or more Tile layers

    This is the "facade" class and hides details of tilesource/storage, and is
    supposed be used by server frontend and rendering scripts.

    """

    def __init__(self):
        self._layers = collections.OrderedDict()

    def add_storage_layer(self, storage):
        tag = storage.metadata.tag
        if tag in self._layers:
            tag = '%s-%d' % (tag, len(self._layers))
        self._layers[tag] = StorageLayer(storage)

    def add_renderer_layer(self, renderer):
        tag = renderer.metadata.tag
        if tag in self._layers:
            tag = '%s-%d' % (tag, len(self._layers))
        self._layers[tag] = RendererLayer(renderer)

    def craft_tile(self, tag, z, x, y):
        """ Craft a tile from renderer or retrieve one from tile storage.

        Returns a tuple of (data, mimetype, mtime).
        data is a bytes array of tile data (usually an image)
        mimetype is data mimetype
        mtime is tile modification time
        """
        try:
            layer = self._layers[tag]
        except KeyError:
            raise InvalidLayer(tag)

        tile = layer.get_tile(z, x, y)
        if tile is None:
            raise TileNotFound('%s/%d/%d/%d' % (tag, z, x, y))

        return tile.data, layer.metadata['format']['mimetype'], tile.mtime

    def craft_metatile(self, tag, z, x, y, stride):
        raise NotImplementedError

    def get_layers(self):
        return self._layers.keys()

    def get_metadata(self, tag):
        try:
            return self._layers[tag].metadata
        except KeyError:
            return {}

    def close(self):
        for layer in self._layers.itervalues():
            layer.close()
