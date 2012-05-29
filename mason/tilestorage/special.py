'''
Created on May 10, 2012

@author: Kotaimen
'''

import os, os.path
import mimetypes

from .tilestorage import TileStorage, NullTileStorage, ReadOnlyTileStorage
from ..core import Tile


class DefaultTileStorage(ReadOnlyTileStorage):

    """ Always return same tile for any get query



    tag
        Name tag of the storage.

    filename
        default tile file

    ext
        filename extension

    mimetype
        Optional, mimetype of tile data, by default, its guessed from
        extension

    """

    def __init__(self, tag,
                 filename='',
                 ext='',
                 mimetype=None):
        ReadOnlyTileStorage.__init__(self, tag)

        self._filename = filename
        assert self._filename
        self._ext = ext
        assert self._ext

        if mimetype is None:
            self._mimetype, _bar = mimetypes.guess_type('foo.%s' % ext)
            if self._mimetype is None:
                raise Exception("Can't guess mimetype from .%s" % ext)
        else:
            self._mimetype = mimetype

        with open(self._filename, 'rb') as fp:
            self._data = fp.read()

        self._metadata = dict(ext=self._ext,
                              mimetype=self._mimetype,
                              mtime=os.stat(self._filename).st_mtime,
                              )

    def get(self, tile_index):
        return Tile(tile_index, self._data, self._metadata)

    def has_all(self, tile_index):
        return True

    def has_any(self, tile_index):
        return True


class CascadeTileStorage(TileStorage):

    """ Chain several TileStorages together

    Currently only allows 2 or 3 storages, operate as a "cascade cache", the
    first storage is a constrained  cache, usually memcached; second is
    slower full storage, the last one looked when tile is not found
    in second one.""


    tag
        Name tag of the storage.

    storages
        A list of tile storages

    readmode
        Optional, controls how tile is read from storages, can be one of:

        cache
            Acts as a layerd cache, tile is read from first storage to last
            storage, and write to previous storage once a tile is found

        Default value is "cache"

    """

    def __init__(self, tag,
                 storages,
                 read_mode='cache',
                 ):
        TileStorage.__init__(self, tag)
        self._readmode = read_mode
        assert self._readmode in ['cache']
        self._storages = storages
        assert len(storages) in [2, 3]
        if len(storages) == 2:
            self._storages.append(NullTileStorage())

    def get(self, tile_index):
        if self._readmode == 'cache':
            for n, storage in enumerate(self._storages):
                tile = storage.get(tile_index)
                if tile is not None:
                    if n == 1:
                        # Write back to cache only if read from tile source
                        self._storages[0].put(tile)
                    return tile
            else:
                return None
        else:
            raise Exception('Unknown read mode')

    def put(self, tile):
        self._storages[1].put(tile)

    def has_all(self, tile_indexes):
        return self._storages[1].has_all(tile_indexes)

    def has_any(self, tile_indexes):
        return self._storages[1].has_any(tile_indexes)

    def put_multi(self, tiles):
        self._storages[1].put_multi(tiles)

    def delete(self, tile_index):
        self._storages[0].delete(tile_index)
        self._storages[1].delete(tile_index)

    def has(self, tile_index):
        return self._storages[1].has(tile_index)

    def flush_all(self):
        for storage in self._storages:
            storage.flush_all()

    def close(self):
        for storage in self._storages:
            storage.close()

