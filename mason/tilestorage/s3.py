'''
Created on Mar 6, 2013

@author: Kotaimen
'''

import boto
import rfc822

from .tilestorage import TileStorage, TileStorageError
from ..core import Tile, tile_coordiante_to_dirname, Pyramid, Metadata


class S3TileStorageError(TileStorageError):
    pass


class S3TileStorage(TileStorage):

    """ Store Tiles in Amazon S3 public cloud object storage.

    You must already created a bucket for tile storage on AWS already.

    """

    def __init__(self,
                 pyramid=None,
                 metadata=None,
                 access_key='blah',
                 secret_key='blah',
                 bucket_name='foobar',
                 root_tag=None,
                 simple=True,):
        TileStorage.__init__(self, pyramid, metadata)

        self._bucket_name = bucket_name
        if root_tag is None:
            root_tag = metadata.tag
        self._tag = root_tag
        self._ext = pyramid.format.extension

        self._conn = boto.connect_s3(\
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            )

        self._bucket = self._conn.get_bucket(bucket_name)

        self._simple = simple

    def _make_key(self, tile_index):
        if self._simple:
            return '%s/%d/%d/%d%s' % (self._tag,
                                      tile_index.z, tile_index.x, tile_index.y,
                                      self._ext)
        else:
            return '%s/%s/%d-%d-%d%s' % (self._tag,
                                         '/'.join(tile_coordiante_to_dirname(*tile_index.coord)),
                                         tile_index.z, tile_index.x, tile_index.y,
                                         self._ext)

    def get(self, tile_index):
        s3key = boto.s3.key.Key(self._bucket)
        s3key.key = self._make_key(tile_index)
        print 'get', s3key.key
        if not s3key.exists():
            return None
        data = s3key.get_contents_as_string()

        if s3key.last_modified:
            modified_tuple = rfc822.parsedate_tz(s3key.last_modified)
            mtime = int(rfc822.mktime_tz(modified_tuple))
        else:
            mtime = 0

        return Tile.from_tile_index(tile_index, data,
                                    fmt=self.pyramid.format,
                                    mtime=mtime)

    def put(self, tile):
        s3key = boto.s3.key.Key(self._bucket)
        s3key.key = self._make_key(tile.index)
        print 'put', s3key.key
        s3key.set_contents_from_string(tile.data)

    def has(self, tile_index):
        s3key = boto.s3.key.Key(self._bucket)
        s3key.key = self._make_key(tile_index)
        return s3key.exists()

    def delete(self, tile_index):
        s3key = boto.s3.key.Key(self._bucket)
        s3key.key = self._make_key(tile_index)
        s3key.delete()

    def close(self):
        self._conn.close()

