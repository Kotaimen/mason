'''
Created on May 3, 2012

@author: Kotaimen
'''

import errno
import gzip
import mimetypes
import os
import os.path
import shutil
import sys
import tempfile

from ..tilelib import Tile, tile_coordiante_to_dirname
from .tilestorage import TileStorage, TileStorageError


class FileSystemTileStorageError(TileStorageError):
    pass


class FileSystemTileStorage(TileStorage):

    """ Store Tiles on file system as individual files

    File system storage does *NOT* save tile metadata. However, mimetype, ext,
    mimetype will be retrieved from file system.

    Parameters:

    tag
        Name tag of the storage.

    root
        Root directory of the storage tree, the directory will be created if
        it does not exist on file system.

    ext
        filename extension which will be used on disk, this always
        overwrite specified in tile metadata.

    mimetype
        Optional, mimetype of tile data, always overwrite specified in
        tile metadata, by default, it is guessed from extension.

    compress
        Optional, whether to compress file using gzip (the written file will
        have .ext.gz as extension), default value is False.
    """

    def __init__(self,
                 tag,
                 root=r'.',
                 ext='dat',
                 mimetype=None,
                 compress=False,
                 ):
        TileStorage.__init__(self, tag)

        # Create root directory if necessary
        if not root:
            raise FileSystemTileStorageError('Must specify directory root')
        self._root = root

        if not os.path.exists(self._root):
            os.mkdir(self._root)

        # Guess mimetype from extension
        if mimetype is None:
            self._mimetype, _bar = mimetypes.guess_type('foo.%s' % ext)
            if self._mimetype is None:
                raise FileSystemTileStorageError("Can't guess mimetype from .%s" % ext)
        else:
            self._mimetype = mimetype
        self._ext = ext

        # Append .gz to extension if compression is on
        self._use_gzip = bool(compress)

        self._basename = '%d-%d-%d.' + self._ext

    def _get_pathname(self, tile_index):
        dirname = os.path.join(*tile_coordiante_to_dirname(*tile_index.coord))
        basename = self._basename % tile_index.coord
        if self._use_gzip:
            basename += '.gz'
        return os.path.join(self._root, dirname, basename)

    def get(self, tile_index):
        pathname = self._get_pathname(tile_index)

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

        # Construct metadata form file status
        metadata = dict(ext=self._ext,
                        mimetype=self._mimetype,
                        mtime=os.stat(pathname).st_mtime,
                        )
        # Create tile object and return it
        return Tile(tile_index, data, metadata)

    def put(self, tile):
        pathname = self._get_pathname(tile.index)

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

        # Make a temp file first
        fd, tempname = tempfile.mkstemp(suffix='tmp',
                                            prefix=basename,
                                            dir=dirname)
        # Close os file handle, we will write using standard file io
        os.close(fd)

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
        return os.path.exists(self._get_pathname(tile_index))

    def delete(self, tile_index):
        pathname = self._get_pathname(tile_index)
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
