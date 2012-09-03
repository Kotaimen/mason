'''
Created on May 2, 2012

@author: Kotaimen
'''

class TileStorageError(Exception):
    pass


class TileStorage(object):

    """ Store Tile in persistence storage or a cache backend """

    def __init__(self,
                 pyramid,
                 metadata,
#                 flush=False,
                 ):
        """ Create a new tile storage or attaching to an existing one.

        Given parameters must match attaching storage.
        """

        self._metadata = metadata
        self._pyramid = pyramid

    # Property ----------------------------------------------------------------

    @property
    def metadata(self):
        return self._metadata

    @property
    def pyramid(self):
        return self._pyramid

    def attach(self):
        pass

    # Getter/Putter -----------------------------------------------------------

    def put(self, tile):
        """ Put given Tile into cache, overwrite existing one if necessary

        When put failed, implementation may choose to raise a
        exception, or just pass silently.
        This behavior is allowed because write operation may
        be asynchronous.
        """
        raise NotImplementedError

    def get(self, tile_index):
        """ Get Tile from given TileIndex

        Return a new Tile object, or None if Tile does not exist in the storage.
        Note given TileIndex may be used to construct new Tile object.
        """
        raise NotImplementedError

    def has(self, tile_index):
        """ Check whether given TileIndex exists in the cache

        Note implementation may provide a better way instead of actually
        retrieve tile data.
        """
        return self.get(tile_index) is not None

    def delete(self, tile_index):
        """ Remove Tile with given TileIndex form storage

        If Tile does not present in storage, this operation has no effect
        """
        raise NotImplementedError

    # Multi --------------------------------------------------------------------

    def put_multi(self, tiles):
        """ Put many tiles into cache in one call

        Note the default implement is *not* atomic. Implementation may
        provide a more efficient way to do this.

        For databases, this is usually done by using "executemany" so
        its faster as well as being atomic.
        """
        for tile in tiles:
            self.put(tile)

    def get_multi(self, tile_indexes):
        """ Get many tile in one call

        Returns found Tiles in a dict which key is TileIndex.
        If no Tile are not found in the storage, returns empty dict.
        """
        all_tiles = ((tile_index, self.get(tile_index)) for tile_index in tile_indexes)
        # Discard those tile is None and return a dict
        return dict((index, tile) for index, tile in all_tiles if tile is not None)

    def delete_multi(self, tile_indexes):
        """ Delete given Tiles in one call """
        for tile_index in tile_indexes:
            self.delete(tile_index)

    def has_all(self, tile_indexes):
        """ Check whether storage has all given tiles """
        return all(self.has(tile_index) for tile_index in tile_indexes)

    def has_any(self, tile_indexes):
        """ Check whether storage has any given tiles """
        return any(self.has(tile_index) for tile_index in tile_indexes)

    def flush_all(self):
        """ Delete all tiles in the storage """
        raise NotImplementedError

    def close(self):
        """ Close the storage """
        pass


#===============================================================================
# Special Tile Storages
#===============================================================================


class NullTileStorage(TileStorage):

    """ A do-nothing TileStorage """

    def put(self, tile):
        pass

    def get(self, tile_index):
        pass

    def delete(self, tile_index):
        pass

    def flush_all(self):
        pass


class ReadOnlyTileStorage(TileStorage):

    """ Base class of read only tile storages """

    def put(self, tile):
        pass

    def put_multi(self, tiles):
        pass

    def delete(self, tile_index):
        pass

    def flush_all(self):
        pass


