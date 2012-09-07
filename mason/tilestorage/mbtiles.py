'''
Created on May 7, 2012

@author: Kotaimen
'''

import sqlite3
import os
import itertools
import threading

from pprint import pprint

from .tilestorage import TileStorage, TileStorageError
from ..core import Tile

#===============================================================================
# SQLite Helper Functions
#===============================================================================


def create_sqlite_database(filename, pyramid, metadata):
    if os.path.exists(filename):
        return

    conn = sqlite3.connect(filename)
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS metadata (name TEXT, value TEXT, PRIMARY KEY (name));

    CREATE TABLE IF NOT EXISTS tiledata (hash TEXT NOT NULL PRIMARY KEY,
                                         data BLOB NOT NULL);

    CREATE INDEX IF NOT EXISTS tiledata_hash ON tiledata(hash);

    CREATE TABLE tileindex (z INTEGER NOT NULL,
                            x INTEGER NOT NULL,
                            y INTEGER NOT NULL,
                            tilehash TEXT NOT NULL,
                            FOREIGN KEY (tilehash) REFERENCES tiledata(hash)
                                ON UPDATE CASCADE
                                ON DELETE SET NULL,
                            PRIMARY KEY (z, x, y) ON CONFLICT REPLACE
                            );

    CREATE INDEX IF NOT EXISTS tileindex_z_x_y ON tileindex(z, x, y);

    CREATE VIEW IF NOT EXISTS tiles AS
                    SELECT z AS zoom_level,
                            x AS tile_column,
                            y AS tile_row,
                            data AS tile_data
                    FROM tileindex, tiledata
                    WHERE tileindex.tilehash=tiledata.hash;
    ''')

    values = dict(name=metadata.tag,
                  format=pyramid.format.extension[1:],
                  version=metadata.version,
                  description=metadata.description,
                  attribution=metadata.attribution,
                  bounds=repr(pyramid.envelope.make_tuple())[1:-1],
                  center='%f,%f,%d' % (pyramid.center.lon, pyramid.center.lat, pyramid.zoom),
                  minzoom=str(min(pyramid.levels)),
                  maxzoom=str(min(pyramid.levels)),
                  )

#    assert values['format'] in ['png', 'jpg']
    pprint(values)

    conn.executemany('INSERT INTO metadata VALUES (?, ?)', values.iteritems())

    conn.commit()
    conn.close()


#===============================================================================
# Storage
#===============================================================================

class MBTilesTileStorageError(TileStorageError):
    pass


class MBTilesTileStorage(threading.local, # sqlite3 is not thread safe
                         TileStorage
                         ):

    """ Using sqlite3 database as tile storage

    This storage implements MBTiles format (http://mapbox.com/mbtiles-spec/).
    MBTiles is a sqlite3 database stores tile images as BLOB data, which is
    nice when managing small-to-medium data sets.  However, when stores billions
    of tiles, a single sqlite3 file is generally not a good choice.

    We supports de-duplication in one Mbtiles database by using pre-calculated
    Tile.hash, so in large sea areas with same color will share only one tile
    data instance, this reduces file size in most situation.

    For details of the spec, check:
        https://github.com/mapbox/mbtiles-spec/blob/master/1.1/spec.md

    database
        Database file name

    timeout
        Optional, timeout in seconds before trying to lock database for write,
        default is 30s (see notes below)

    Note on timeout: Sqlite3 has a global write lock, even in different
    processes. So when inserting tiles concurrently fast enough, write
    hunger may occur when every process/thread is waiting for the lock.
    Set timeout longer may help reduce "write timeout" problem.

    Note on tile_row: mbtiles 1.1 has *reversed* y axis, hence Tile.index.y
    in mbtiles is 2^z-y-1, this is awkward and is supposed to be fixed in 1.2.
    """
    def __init__(self,
                 pyramid=None,
                 metadata=None,
                 database='',
                 timeout=30,
                 ):
        TileStorage.__init__(self, pyramid, metadata)

        self._database = database

        # Create the database when necessary
        create_sqlite_database(self._database, pyramid, metadata)

        # Connect to database
        self._timeout = timeout
        self._conn = sqlite3.connect(self._database,
                                     timeout=self._timeout)

        # Use database file mtime as Tile mtime
        self._mtime = os.stat(self._database).st_mtime

        # Close and reset the connection
        self._conn.close()
        self._conn = None

    def _get_conn(self):
        # NOTE: This is necessary because sqlite3 is not thread safe, and
        #       connection object can only be used in the thread it was
        #       created.  To solve this we use TLS and lazy initialization
        if self._conn is None:
            self._conn = sqlite3.connect(self._database, timeout=self._timeout)
        return self._conn

    def _make_mbtiles_index(self, tile_index):
        # Mbtiles has reversed y-axis, which differs with every other format...
        z, x, y = tile_index.coord
        return z, x, 2 ** z - y - 1

    def get(self, tile_index):
        z, x, y = self._make_mbtiles_index(tile_index)
        conn = self._get_conn()
        with conn:
            cur = conn.execute('''
                SELECT tile_data FROM tiles
                WHERE zoom_level=? AND tile_column=? AND tile_row=?
                ''',
                (z, x, y))
            row = cur.fetchone()
            if row is None:
                return None
            data = bytes(row[0])

            return Tile.from_tile_index(tile_index, data,
                                        fmt=self.pyramid.format,
                                        mtime=self._mtime)

    def put(self, tile):
        z, x, y = self._make_mbtiles_index(tile.index)

        tile_hash = tile.data_hash
        data = buffer(tile.data)

        conn = self._get_conn()
        with conn:
            cur = conn.cursor()
            cur.execute('''
                INSERT OR REPLACE INTO
                tiledata(hash, data)
                VALUES (?, ?)''',
                (tile_hash, data))

            cur.execute('''
                INSERT OR REPLACE INTO
                tileindex(z, x, y, tilehash)
                VALUES (?, ?, ?, ?)''',
                (z, x, y, tile_hash))

    def has(self, tile_index):
        z, x, y = self._make_mbtiles_index(tile_index)
        conn = self._get_conn()
        with conn:
            cur = conn.execute('''
                SELECT z FROM tileindex WHERE
                (z=? AND x=? AND y=?)''',
                (z, x, y))
            row = cur.fetchone()
            return row is not None

    def delete(self, tile_index):
        z, x, y = self._make_mbtiles_index(tile_index)
        conn = self._get_conn()
        with conn:
            conn.execute('''
                DELETE FROM tileindex
                WHERE (z=? AND x=? AND y=?)''',
                (z, x, y))

    def set_multi(self, tiles):
        hashes = list(tile.data_hash for tile in tiles)

        def data_gen():
            for hash_, tile in itertools.izip(hashes, tiles):
                yield hash_, buffer(tile.data)

        def index_gen():
            for hash_, tile in itertools.izip(hashes, tiles):
                z, x, y = self._make_mbtiles_index(tile.index)
                yield z, x, y, hash, buffer(tile.data)

        conn = self._get_conn()
        with conn:
            cur = conn.cursor()
            cur.executemany('''
                INSERT OR REPLACE INTO
                tiledata(hash, data)
                VALUES (?, ?)''',
                data_gen())

            cur.executemany('''
                INSERT OR REPLACE INTO
                tileindex(z, x, y, tilehash)
                VALUES (?, ?, ?, ?)''',
                index_gen())

    def has_all(self, tile_indexes):
        conn = self._get_conn()
        with conn:
            for tile_index in tile_indexes:
                z, x, y = self._make_mbtiles_index(tile_index)
                cur = conn.execute('''
                SELECT z FROM tileindex WHERE
                (z=? AND x=? AND y=?)''',
                (z, x, y))
                row = cur.fetchone()
                if row is None:
                    return False
            else:
                return True

    def flush_all(self):
        pass

    def close(self):
        conn = self._get_conn()
        conn.close()
        self._conn = None
