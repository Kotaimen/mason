'''
Created on Aug 31, 2012

@author: Kotaimen
'''
import os
import gzip
import json
from ..core import (MetaTile, MetaTileIndex, tile_coordiante_to_dirname,
                    Pyramid, Metadata)

from .filesystem import FileSystemTileStorage


class MetaTileCache(FileSystemTileStorage):

    """ Cache MetaTile render results

    Currently the cache is put on filesystem as tree of files
    """

    CONFIG_VERSION = 'metacache-1.0.0'

    def __init__(self,
                 pyramid,
                 metadata,
                 root,
                 compress=False,
                 simple=False):
        FileSystemTileStorage.__init__(self, pyramid, metadata, root,
                                       compress=compress, simple=False)
        assert not simple

    @staticmethod
    def from_config(root):
        config_file = os.path.join(root, FileSystemTileStorage.CONFIG_FILENAME)
        with open(config_file, 'r') as fp:
            summary = json.load(fp)
            return MetaTileCache.from_summary(summary, root)

    @staticmethod
    def from_summary(summary, root):
        summary = dict(summary) # copy dict object
        summary['root'] = root
        summary['pyramid'] = Pyramid.from_summary(summary['pyramid'])
        summary['metadata'] = Metadata.from_dict(summary['metadata'])
        assert summary.pop('magic') == MetaTileCache.CONFIG_VERSION
        return MetaTileCache(**summary)

    def _make_pathname(self, metatile_index):
        assert not self._simple
        basename = '%d-%d-%d@%d%s' % (metatile_index.z,
                                      metatile_index.x,
                                      metatile_index.y,
                                      metatile_index.stride,
                                      self._ext)
        dirname = os.path.join(*tile_coordiante_to_dirname(*metatile_index.coord))
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

        mtime = os.stat(pathname).st_mtime

        # Create tile object and return it
        return MetaTile.from_tile_index(tile_index, data,
                                        fmt=self.pyramid.format,
                                        mtime=mtime)

    def put(self, tile):
        assert isinstance(tile, MetaTile)
        return FileSystemTileStorage.put(self, tile)

    def has(self, tile_index):
        return os.path.exists(self._make_pathname(tile_index))

    def delete(self, tile_index):
        FileSystemTileStorage.delete(self, tile_index)
