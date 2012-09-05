'''
Created on May 3, 2012

@author: Kotaimen
'''

import errno
import gzip
import os
import shutil
import sys
import tempfile
import json

from .tilestorage import TileStorage, TileStorageError
from ..core import Tile, tile_coordiante_to_dirname, Pyramid, Metadata
from ..utils.adhoc import create_temp_filename


class FileSystemTileStorageError(TileStorageError):
    pass


class FileSystemTileStorage(TileStorage):

    """ Store Tiles on file system as individual files

    Parameters:

    root
        Root directory of the storage tree, the directory will be created if
        it does not exist on file system.

    compress
        Optional, whether to compress file using gzip (file will
        use .ext.gz as extension), default value is None.

    simple
        Optional, whether to use simple directory theme (z/x/y.ext), useful
        when serving small number of tiles (or serve direct from a static file
        server), default is False.

    """

    CONFIG_VERSION = 1
    CONFIG_FILENAME = 'metadata.json'

    def __init__(self,
                 pyramid=None,
                 metadata=None,
                 root=None,
                 compress=False,
                 simple=False,
                 ):
        assert pyramid is not None
        assert metadata is not None

        TileStorage.__init__(self, pyramid, metadata)
        assert root is not None

        self._root = root
        if not os.path.exists(self._root):
            os.mkdir(self._root)

        self._use_gzip = bool(compress)
        self._simple = simple

        self._config = os.path.join(self._root, self.CONFIG_FILENAME)
        if os.path.exists(self._config):
            if self.compare_config():
                raise FileSystemTileStorageError('Given config does not match existing one')
        else:
            self.write_config()

        self._ext = pyramid.format.extension
        self._use_gzip = bool(compress)
#        self._basename = '%d-%d-%d' + self._ext

    # Config serialization -----------------------------------------------------
    def summarize(self):
        return dict(version=self.CONFIG_VERSION,
                    pyramid=self._pyramid.summarize(),
                    metadata=self._metadata.make_dict(),
                    compress=self._use_gzip,
                    simple=self._simple,
                    )

    @staticmethod
    def from_summary(summary, root):
        summary = dict(summary)  # copy dict object
        summary['root'] = root
        summary['pyramid'] = Pyramid.from_summary(summary['pyramid'])
        summary['metadata'] = Metadata.from_dict(summary['metadata'])
        return FileSystemTileStorage(**summary)

    def write_config(self):
        summary = self.summarize()
        with open(self._config, 'w') as fp:
            json.dump(summary, fp, indent=4)

    def compare_config(self):
        with open(self._config, 'r') as fp:
            disk_summary = json.loads(fp)
            my_summary = self.summarize()
            return my_summary == disk_summary

    @staticmethod
    def from_config(self, config_filename):
        with open(self._config, 'r') as fp:
            summary = json.loads(fp)
            root = os.path.dirname(config_filename)
            return FileSystemTileStorage(summary, root)

    # Aux --------------------------------------------------------------------

    def _make_pathname(self, tile_index):

        if self._simple:
            basename = '%d%s' % (tile_index.y, self._ext)
            dirname = os.path.join(str(tile_index.z), str(tile_index.x))
        else:
            basename = '%d-%d-%d%s' % (tile_index.z, tile_index.x, tile_index.y, self._ext)
            dirname = os.path.join(*tile_coordiante_to_dirname(*tile_index.coord))
        if self._use_gzip:
            basename += '.gz'
        return os.path.join(self._root, dirname, basename)

    def get(self, tile_index):
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
        return Tile.from_tile_index(tile_index, data,
                                    fmt=self.pyramid.format,
                                    mtime=mtime)

    def put(self, tile):

        pathname = self._make_pathname(tile.index)

        # Create directory first
        dirname = os.path.dirname(pathname)
        basename = os.path.basename(pathname)
        if not (os.path.exists(pathname) and os.path.isdir(pathname)):
            try:
                os.makedirs(dirname)
            except OSError as e:
                if e.errno == errno.EEXIST:
                    # HACK: Ignore "already exists" error because os.makedirs 
                    #       does not check dir exists at each creation step
                    pass
                else:
                    raise

        tempname = create_temp_filename(suffix='.tmp~',
                                        prefix=basename,
                                        dir=dirname,
                                        )
        if self._use_gzip:
            with gzip.GzipFile(tempname, 'wb') as fp:
                fp.write(tile.data)
        else:
            with open(tempname, 'wb') as fp:
                fp.write(tile.data)

        if sys.platform == 'win32':  # platform.platform is too verbose
            if os.path.exists(pathname):
                # os.rename is not atomic and requires target
                # file not exist on windows
                os.remove(pathname)
        os.rename(tempname, pathname)

    def has(self, tile_index):
        return os.path.exists(self._make_pathname(tile_index))

    def delete(self, tile_index):
        pathname = self._make_pathname(tile_index)
        try:
            os.remove(pathname)
        except OSError as e:
            if e.errno == errno.ENOENT:
                # File not found is really not an error here
                pass
            else:
                raise

    def flush_all(self):
        if os.path.exists(self._root):
            shutil.rmtree(self._root)
