'''
Created on May 3, 2012

@author: Kotaimen
'''

import memcache

from .tilestorage import TileStorage, TileStorageError


class MemCachedTileStorageError(TileStorageError):
    pass


class MemCachedTileStorage(TileStorage):

    """ Store Tiles in memcached distributed key/value store

    Note any storage which talks memcached protocal is supported,
    like couchbase.

    tag
        Name tag of the storage.

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
                 tag,
                 servers=['localhost:11211'],
                 compress=False,
                 timeout=0,
                 max_size=1024 * 1024,
                 ):
        TileStorage.__init__(self, tag)

        # Create memcached client
        self._client = memcache.Client(servers,
                                       pickleProtocol= -1, # use highest protocal
                                       server_max_value_length=max_size,
                                       )

        # Test connection here
        if not self._client.get_stats():
            raise MemCachedTileStorageError("Can't connect to memcached: %s" % servers)

        self._timeout = timeout
        self._compress = 1024 if compress else 0

    def _make_key(self, tile_index):
        # Include tag in the index so differnt storage can share one memcache bucket
        return '%s/%d/%d/%d' % (self._tag, tile_index.z, tile_index.x, tile_index.y)

    def get(self, tile_index):
        key = self._make_key(tile_index)
        return self._client.get(key)

    def put(self, tile):
        key = self._make_key(tile.index)
        self._client.set(key, tile,
                         self._timeout,
                         self._compress)

    def delete(self, tile_index):
        key = self._make_key(tile_index)
        self._client.delete(key)


    def flush_all(self):
        self._client.flush_all()
