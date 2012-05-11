'''
Created on May 10, 2012

@author: Kotaimen
'''

import os, os.path
import mimetypes

from .tilestorage import TileStorage, ReadOnlyTileStorage
from ..tilelib import Tile


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
        ReadOnlyTileStorage.__init__(tag)

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
            self._data(fp.read())

        self._metadata = dict(ext=self._ext,
                              mimetype=self._mimetype,
                              mtime=os.stat(self._filename).st_mtime,
                              )

    def get(self, tile_index):
        return Tile(tile_index, self._data, self._metadata)


class CascadeTileStorage(TileStorage):

    """ Chain several TileStorages together



    tag
        Name tag of the storage.

    storages
        A list of tile storages

    readmode
        Optional, controls how tile is read from storages, can be one of:

        cache
            Acts as a layerd cache, tile is read from first storage to last
            storage, and write to previous storage once a tile is found

        top
            Act as a "top" view, data is read from last storage to first
            storage

        Default value is "cache"

    writemode
        Optional, controls how tile is write to storages, can be one of:

        sync
            Tile is written to all stroages

        last
            Tile is written to last storage only, tile in previous storage
            is deleted

        Default value is "cache"

    """

    def __init__(self, tag,
                 storages,
                 read_mode='cache',
                 write_mode='last',
                 ):
        TileStorage.__init__(self, tag)
        self._readmode = read_mode
        assert self._readmode in ['cache', 'top']
        self._writemode = write_mode
        assert self._writemode in ['sync', 'last']
        self._storages = storages
        assert len(self._storages) > 1

    def get(self, tile_index):
        if self._readmode == 'cache':
            for n, storage in enumerate(self._storages):
                tile = storage.get(tile_index)
                if tile is not None:
                    for m in range(0, n):
                        self._storages[m].put(tile)
                    return tile
            else:
                return None

        elif self._readmode == 'top':
            for storage in reversed(self._storages):
                tile = storage.get(tile_index)
                if tile is not None:
                    return tile
        else:
            raise Exception('Unknown read mode')

    def put(self, tile):
        if self._writemode == 'sync':
            for storage in self._storages:
                storage.put(tile)
        elif self._writemode == 'last':
            self._storages[-1].put(tile)
        else:
            raise Exception('Unknown write mode')

    def delete(self, tile_index):
        for storage in self._storages:
            storage.delete(tile_index)

    def has(self, tile_index):
        return any(storage.has(tile_index) for storage in self._storages)

    def flush_all(self):
        for storage in self._storages:
            storage.flush_all()

    def close(self):
        for storage in self._storages:
            storage.close()

