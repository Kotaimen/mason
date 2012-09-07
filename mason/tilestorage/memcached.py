###
### XXX : NEED REWRITTEN TO CONFRONT NEW IF
###

'''
Created on May 3, 2012

@author: Kotaimen
'''

import memcache

from .tilestorage import TileStorage, TileStorageError


class MemcachedTileStorageError(TileStorageError):
    pass


class MemcachedTileStorage(TileStorage):

    """ Store Tiles in memcached distributed key/value store

    Note any storage which talks memcached protocal is supported,
    like couchbase.

    servers
        Optional, list of memcached servers, default is ['localhost:11211',]

    compress
        Optional, whether to compress content using memcache client, (memcached
        has a default 1M item limit), default is false

    timeout
        Optional, time in seconds before items are retired by memcached,
        default is 0, means no expiration.

    max_size
        Optional, max size of memcached object size in bytes.  Memcached has
        limit of 1M, couchbase has a limit of 64M, default value is 1M.
        Note this size is the pickled object size, not size of Tile.data

    """

    def __init__(self,
                 pyramid=None,
                 metadata=None,
                 servers=['localhost:11211'],
                 compress=False,
                 timeout=0,
                 max_size=1024 * 1024,
                 ):
        TileStorage.__init__(self, pyramid, metadata)

        # Create memcached client, use highest pickle protocol
        self._client = memcache.Client(servers,
                                       pickleProtocol= -1,
                                       server_max_value_length=max_size,
                                       )

        # Test connection here
        if not self._client.get_stats():
            raise MemcachedTileStorageError("Can't connect to memcached: %s" % servers)

        self._timeout = timeout
        self._compress = 1024 if compress else 0

    def _make_key(self, tile_index):
        # Include tag in the index so differnt storage can share one memcache bucket
        return '%s/%d/%d/%d' % (self._metadata.tag, tile_index.z, tile_index.x, tile_index.y)

    def get(self, tile_index):
        key = self._make_key(tile_index)
        return self._client.get(key)

    def put(self, tile):
        key = self._make_key(tile.index)
        self._client.set(key, tile,
                         time=self._timeout,
                         min_compress_len=self._compress)

    def has(self, tile_index):
        key = self._make_key(tile_index)
        return self._client.get(key) is not None

    def delete(self, tile_index):
        key = self._make_key(tile_index)
        self._client.delete(key)

    def get_multi(self, tile_indexes):
        # Make key->tile_index map
        key2tile = dict((self._make_key(tile_index), tile_index) for \
                         tile_index in tile_indexes)
        # Get key->value map
        key2value = self._client.get_multi(key2tile.keys())
        # Replace key with tile_index
        return dict((key2tile[k], v) for k, v in key2value.iteritems())

    def set_multi(self, tiles):
        keys = list(self._make_key(tile.index) for tile in tiles)
        # Key 2 tile mapping
        key2tile = dict(zip(keys, tiles))

        failed = self._client.set_multi(key2tile,
                                        time=self._timeout,
                                        min_compress_len=self._compress)

        if failed:
            raise MemcachedTileStorageError('%d items not written' % len(failed))

    def del_multi(self, tile_indexes):
        keys = list(self._make_key(tile_index) for tile_index in tile_indexes)
        self._client.delete_multi(keys)

    def has_all(self, tile_indexes):
        keys = list(self._make_key(tile_index) for tile_index in tile_indexes)
        mapping = self._client.get_multi(keys)
        if not mapping:
            return False
        return set(mapping.keys()) == set(keys)

    def flush_all(self):
        self._client.flush_all()

    def close(self):
        self._client.disconnect_all()

