'''
Created on Jan 14, 2013

@author: Kotaimen
'''

import os
import zipfile
from io import BytesIO
import copy

try:
    import simplejson as json
except ImportError:
    import json

from ..core import (MetaTile, MetaTileIndex, tile_coordiante_to_dirname,
                    Pyramid, Metadata, Format)

from .tilestorage import TileStorage, TileStorageError, NullTileStorage
from .memcached import MemcachedTileStorage
from .filesystem import FileSystemTileStorage


class TileCluster(object):

    """ Store tiles together by cluster them in a zip file and
    remove duplicated tile data.

    Zip file is choosen because there is no way to write a tar file
    cross-platform using python standard libraries.
    """

    INDEX = 'tiles.json'

    def __init__(self,
                 pyramid, tiles):
        self._pyramid = pyramid
        self._ext = pyramid.format.extension
        self._tiles = tiles

    def fusion(self, compression=False):
        keys = list('%d-%d-%d' % tile.index.coord for tile in self._tiles)
        hashes = list(tile.data_hash for tile in self._tiles)
        datas = list(tile.data for tile in self._tiles)

        # Key->Data map for write zip file
        mapping = dict(zip(keys, datas))

        # Build a key->key dedup dict and delete duplicated from mapping
        dedup = dict()
        for i in range(len(self._tiles)):
            k = keys[i]
            h = hashes[i]
            try:
                j = hashes[0:i].index(h)  # use first data has same hash
                dedup[k] = keys[j]
                del mapping[k]
            except ValueError:
                dedup[k] = k

        # Write zipfile in memory as buffer
        zipbuf = BytesIO()
        compression = zipfile.ZIP_DEFLATED if compression else zipfile.ZIP_STORED
        zipobj = zipfile.ZipFile(file=zipbuf, mode='w')

        index = {'tiles': dedup, 'datas': mapping.keys(), 'extension': self._ext }

        zipobj.writestr(self.INDEX, json.dumps(index, indent=2))
        for k, data in mapping.iteritems():
            zipobj.writestr(k + self._ext, data)
        zipobj.close()

        return zipbuf.getvalue()

    @staticmethod
    def fission(pyramid, buf):
        stream = BytesIO(buf)
        zip_file = zipfile.ZipFile(file=stream, mode='r')
        index = json.loads(zip_file.read(TileCluster.INDEX))
        datas = dict()

        for k in index['datas']:
            datas[k] = zip_file.read(k + index['extension'])
        tiles = list()
        for k, v in index['tiles'].iteritems():
            z, x, y = tuple(map(int, k.split('-')))
            tile = pyramid.create_tile(z, x, y, datas[v])
            tiles.append(tile)

        return tiles


class ClusterTileStorage(FileSystemTileStorage):

    """ Store adjacent tiles in a cluster """

    CONFIG_VERSION = 'cluster-1.0.0'

    def __init__(self,
                 pyramid=None,
                 metadata=None,
                 stride=4,
                 servers=None,
                 timeout=0,
                 root='',
                 compress=False,
                 ):
        self._stride = stride
        self._compress = compress
        self._timeout = timeout
        self._servers = servers

        FileSystemTileStorage.__init__(self, pyramid, metadata, root,)
        if servers is not None:
            self._cache = MemcachedTileStorage(pyramid,
                                               metadata,
                                               servers=servers,
                                               timeout=timeout,
                                               compress=compress)
        else:
            self._cache = NullTileStorage()

    # Config serialization -----------------------------------------------------

    def summarize(self):
        return dict(magic=self.CONFIG_VERSION,
                    pyramid=self._pyramid.summarize(),
                    metadata=self._metadata.make_dict(),
                    compress=self._compress,
                    stride=self._stride,
                    servers=self._servers,
                    timeout=self._timeout,
                    )

    @staticmethod
    def from_config(root):
        config_file = os.path.join(root, ClusterTileStorage.CONFIG_FILENAME)
        with open(config_file, 'r') as fp:
            summary = json.load(fp)
            return ClusterTileStorage.from_summary(summary, root)

    @staticmethod
    def from_summary(summary, root):
        summary = dict(summary)  # copy dict object
        summary['root'] = root
        summary['pyramid'] = Pyramid.from_summary(summary['pyramid'])
        summary['metadata'] = Metadata.from_dict(summary['metadata'])
        assert summary.pop('magic') == ClusterTileStorage.CONFIG_VERSION
        return ClusterTileStorage(**summary)

    # Aux ---------------------------------------------------------------------

    def _make_pathname(self, metatile_index):
        assert not self._simple
        basename = '%d-%d-%d@%d.zip' % (metatile_index.z,
                                        metatile_index.x,
                                        metatile_index.y,
                                        metatile_index.stride)
        dirname = os.path.join(*tile_coordiante_to_dirname(*metatile_index.coord))
        return os.path.join(self._root, dirname, basename)

    # Getter/Setter -----------------------------------------------------------

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

        metatile = FileSystemTileStorage.get(self, metatile_index)

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

                # XXX: is this too expensive?
#                for tile in tiles[1:]:
#                    idx = self._pyramid.create_metatile_index(tile.index.z,
#                                                              tile.index.x,
#                                                              tile.index.y,
#                                                              self._stride)
#                    assert metatile.index == idx

        FileSystemTileStorage.put(self, metatile)

    def has(self, tile_index):
        return self._cache.has(tile_index)

    def has_all(self, tile_indexes):
        # NOTE: This is a "has_any" check
        metatile_index = self._pyramid.create_metatile_index(tile_indexes[0].z,
                                                             tile_indexes[0].x,
                                                             tile_indexes[0].y,
                                                             self._stride)
        return FileSystemTileStorage.has(self, metatile_index)

    def delete(self, tile_index):
        self._cache.delete(tile_index)

