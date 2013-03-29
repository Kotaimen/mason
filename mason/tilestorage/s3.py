'''
Created on Mar 6, 2013

@author: Kotaimen
'''

import boto
import rfc822

from .tilestorage import TileStorage, TileStorageError
from .cluster import TileCluster
from .memcached import MemcachedTileStorage
from ..core import Tile, tile_coordiante_to_dirname, Pyramid, Metadata
from ..utils import human_size


class S3TileStorageError(TileStorageError):
    pass


class S3TileStorage(TileStorage):

    """ Store Tiles in Amazon S3 public cloud object storage.

    Set access_key and secret_key to None to use key defined in environment
    variable AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
    """

    def __init__(self,
                 pyramid=None,
                 metadata=None,
                 access_key='blah',
                 secret_key='blah',
                 bucket_name='foobar',
                 root_tag=None,
                 simple=False,
                 ):
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
#        print 'get', s3key.key
        if not s3key.exists():
            # Check key existence first otherwise get_content will retry several
            # times, which slows thing down, note this is not atomic
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
#        print 'put', s3key.key, human_size(len(tile.data))
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


class S3ClusterTileStorage(S3TileStorage):

    # XXX: This is not inherited from FileClusterTileStorage, keep until
    #      we can absorb the difference between NFS and S3

    def __init__(self,
                 pyramid=None,
                 metadata=None,
                 stride=4,
                 servers=['localhost:11211'],
                 timeout=0,
                 access_key='blah',
                 secret_key='blah',
                 bucket_name='foobar',
                 root_tag=None,
                 compress=False,
                 ):

        self._stride = stride
        self._compress = compress
        self._timeout = timeout
        self._servers = servers

        S3TileStorage.__init__(self,
                               pyramid, metadata, access_key, secret_key,
                               bucket_name, root_tag)

        self._cache = MemcachedTileStorage(pyramid,
                                           metadata,
                                           servers=servers,
                                           timeout=timeout,
                                           compress=compress)

    def _make_key(self, metatile_index):
        assert not self._simple
        return '%s/%s/%d-%d-%d@%d.zip' % (self._tag,
                                          '/'.join(tile_coordiante_to_dirname(*metatile_index.coord)),
                                           metatile_index.z,
                                           metatile_index.x,
                                           metatile_index.y,
                                           self._stride)

    def get(self, tile_index):
        # Try tie1 cache first
        tile = self._cache.get(tile_index)
        if tile is not None:
            return tile

        # Then lookup tie2 cluster
        metatile_index = self._pyramid.create_metatile_index(tile_index.z,
                                                             tile_index.x,
                                                             tile_index.y,
                                                             self._stride)

        metatile = S3TileStorage.get(self, metatile_index)

        if metatile is None:
            return None

        tiles = TileCluster.fission(self._pyramid, metatile.data)

        # Write back tiles to tile1 cache and return requested tile
        self._cache.put_multi(tiles)

        # Return requested tile
        for tile in tiles:
            if tile.index == tile_index:
                return tile
        else:
            return None

    def put(self, tile):
        # Only write to tie1 cache when put single tile
        self._cache.put(tile)

    def put_multi(self, tiles):
        assert isinstance(tiles, list)

        # Assuming we are putting single tile into cache
        if tiles[0] > 0 and len(tiles) == 1:
            self.put(tiles[0])
            return

        # Otherwise, create a cluster form given tiles
        cluster = TileCluster(self._pyramid, tiles)
        buf = cluster.fusion(compression=self._compress)
        metatile = self._pyramid.create_metatile(tiles[0].index.z,
                                                 tiles[0].index.x,
                                                 tiles[0].index.y,
                                                 self._stride,
                                                 buf)
        # Assume tiles comes from a single MetaTile
        if  2 ** tiles[0].index.z >= self._stride:
            if len(tiles) != self._stride * self._stride:
                raise TileStorageError('Must put a fissioned MetaTile into cluster storage, '
                                       'set render stride equal to cluster stride.')

        S3TileStorage.put(self, metatile)

    def has(self, tile_index):
        return self._cache.has(tile_index)

    def has_all(self, tile_indexes):
        # NOTE: This is a "has_any" check
        metatile_index = self._pyramid.create_metatile_index(tile_indexes[0].z,
                                                             tile_indexes[0].x,
                                                             tile_indexes[0].y,
                                                             self._stride)
        return S3TileStorage.has(self, metatile_index)

    def delete(self, tile_index):
        self._cache.delete(tile_index)


