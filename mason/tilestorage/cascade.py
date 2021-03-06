'''
Created on Dec 5, 2012

@author: Kotaimen
'''


from .tilestorage import TileStorage, TileStorageError


class CascadeTileStorage(TileStorage):

    """ Hybrid tile storage combines a persistent storage and a violate storage """

    def __init__(self, pyramid, metadata,
                 violate=None,
                 presistent=None,
                 write_back=False
                 ):
        TileStorage.__init__(self, pyramid, metadata)
        self._storages = [violate, presistent]
        self._writeback = write_back

    def get(self, tile_index):
        for n, storage in enumerate(self._storages):
            tile = storage.get(tile_index)
            if tile is not None:
                if n == 1:
                    # Write back to cache only if read from persistent source
                    self._storages[0].put(tile)
                return tile
        else:
            return None

    def put(self, tile):
        # Only write to violate storage one put one tile
        if self._writeback:
            self._storages[1].put(tile)
        self._storages[0].put(tile)

    def has_all(self, tile_indexes):
        return self._storages[0].has_all(tile_indexes)

    def has_any(self, tile_indexes):
        return self._storages[0].has_any(tile_indexes)

    def put_multi(self, tiles):
        if self._writeback:
            self._storages[1].put_multi(tiles)
        self._storages[0].put_multi(tiles)

    def delete(self, tile_index):
        self._storages[0].delete(tile_index)
        self._storages[1].delete(tile_index)

    def has(self, tile_index):
        return self._storages[0].has(tile_index)

    def flush_all(self):
        for storage in self._storages:
            storage.flush_all()

    def close(self):
        for storage in self._storages:
            storage.close()
