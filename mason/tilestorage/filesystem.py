'''
Created on May 3, 2012

@author: Kotaimen
'''

import os
import os.path
import gzip
import re


from .tilestorage import TileStorage


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

    sharding
        Optional, whether store tile in directory directly using z/x/y or
        split into a directory tree.  Default is True, which means enable
        direcory sharding.

    mimetype
        Optional, mimetype of tile data, always overwrite specified in
        tile metadata, by default, it is guessed from extension.

    compress
        Optional, whether to compress file using gzip (the written file will
        have .ext.gz as extension), default value is 0, means no compression.
        An integer from 1 to 9 means the level of compression, 1 is fastest
        9 is slowest compress most, recommended value is 6.
    """

    def __init__(self,
                 tag,
                 root=r'.',
                 ext='dat',
                 sharding=True,
                 mimetype=None,
                 compress=0,
                 ):
        TileStorage.__init__(tag)

