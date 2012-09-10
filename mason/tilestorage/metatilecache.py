'''
Created on Aug 31, 2012

@author: Kotaimen
'''
import os
import gzip
from ..core import MetaTile, MetaTileIndex, tile_coordiante_to_dirname

from .filesystem import FileSystemTileStorage


class MetaTileCache(FileSystemTileStorage):

    """ Cache MetaTile render results

    Currently the cache is put on filesystem as a directory tree
    """

    def __init__(self,
                 pyramid,
                 metadata,
                 root,
                 compress=False):
        FileSystemTileStorage.__init__(self, pyramid, metadata, root,
                                       compress=compress, simple=False)

    def _make_pathname(self, tile_index):
        assert not self._simple
        basename = '%d-%d-%d@%d%s' % (tile_index.z, tile_index.x, tile_index.y,
                                      tile_index.stride, self._ext)
        dirname = os.path.join(*tile_coordiante_to_dirname(*tile_index.coord))
        if self._use_gzip:
            basename += '.gz'
        return os.path.join(self._root, dirname, basename)

    def get(self, tile_index):
        assert isinstance(tile_index, MetaTileIndex)
        pathname = self._make_pathname(tile_index)

        if not os.path.exists(pathname):
            # Tile does not exist
            return None

        if self._use_gzip:
            # Read using gzip if data is compressed
            with gzip.GzipFile(pathname, 'rb') as fp:
                data = fp.read()
        else:
            # Otherwise, read from file
            with open(pathname, 'rb') as fp:
                data = fp.read()

        mtime = os.stat(pathname).st_mtime,

        # Create tile object and return it
        return MetaTile.from_tile_index(tile_index, data,
                                        fmt=self.pyramid.format,
                                        mtime=mtime)

    def put(self, tile):
        assert isinstance(tile, MetaTile)
        return FileSystemTileStorage.put(self, tile)

    def has(self, tile_index):
        return os.path.exists(self._make_pathname(tile_index))
