'''
Created on May 7, 2012

@author: Kotaimen
'''

import sqlite3
import os, os.path
import json
import mimetypes
import itertools
import threading

from .tilestorage import TileStorage, TileStorageError
from ..tilelib import Tile

#===============================================================================
# SQLite Helper Functions
#===============================================================================


def create_sqlite_database(filename, tag, ext):
    if os.path.exists(filename):
        return

    conn = sqlite3.connect(filename)
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS metadata (name TEXT, value TEXT, PRIMARY KEY (name));
    INSERT INTO metadata VALUES('name', '%(name)s');
    INSERT INTO metadata VALUES('type', 'overlay');
    INSERT INTO metadata VALUES('version', '');
    INSERT INTO metadata VALUES('description', '');
    INSERT INTO metadata VALUES('format', '%(format)s');

    CREATE TABLE IF NOT EXISTS tiledata (hash TEXT NOT NULL PRIMARY KEY,
                                         data BLOB NOT NULL);

    CREATE INDEX IF NOT EXISTS tiledata_hash ON tiledata(hash);

    CREATE TABLE tileindex (z INTEGER NOT NULL,
                            x INTEGER NOT NULL,
                            y INTEGER NOT NULL,
                            tilehash TEXT NOT NULL,
                            metadata BLOB NOT NULL,
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
                            data AS tile_data,
                            metadata
                    FROM tileindex, tiledata
                    WHERE tileindex.tilehash=tiledata.hash;


    ''' % {'format':ext, 'name':tag})
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

    ext
        Image format, theoretically can only be png or jpg (required by
        Mbtiles spec).
        In practical, any content type can be stored in the database (its
        just a BLOB).

    mimetype
        Optional, mimetype of tile data, always overwrite specified in
        tile metadata, by default, it is guessed from extension.

    timeout
        Optional, timeout in seconds before trying to lock database for write,
        default is 30s (see notes below)

    Note on timeout: Sqlite3 has a global write lock, even in different
    processes. So when inserting tiles concurrently fast enough, write
    hunger may occur when every process/thread is waiting for the lock.
    Set timeout longer may help reduce "write timeout" problem.

    Note on metadata: tile metadata is stored in an additional column in tile
    index table, ext and metadata field is ignored and will not be stored in
    the database to save space, value specified in the CTOR will be used.
    (this imply every tile stored in the storage will have same ext/mimetype,
    like FileSystemTileStorage).

    Note on tile_row: mbtiles 1.1 has *reversed* y axis, hence Tile.index.y
    in mbtiles is 2^z-y-1, this is awkward and is supposed to be fixed in 1.2.
    """
    def __init__(self,
                 tag,
                 database='',
                 ext='png',
                 mimetype=None,
                 timeout=30,
                 ):
        TileStorage.__init__(self, tag)

        self._database = database

        # Guess mimetype from extension
        self._ext = ext
        if mimetype is None:
            self._mimetype, _unused = mimetypes.guess_type('foo.%s' % ext)
            if self._mimetype is None:
                raise MBTilesTileStorageError("Can't guess mimetype from .%s" % ext)
        else:
            self._mimetype = mimetype

        # Create the database when necessary
        create_sqlite_database(self._database, tag, ext)

        # Connect to database
        self._timeout = timeout
        self._conn = sqlite3.connect(self._database,
                                     timeout=self._timeout)

        # Try determinate whether the database is a standard Mbtiles file
        # or our custom format (somewhat akward code)
        try:
            self._conn.execute('SELECT metadata FROM tiles LIMIT 1',
                               )

        except sqlite3.Error:
            try:
                self._conn.execute('SELECT tile_data FROM tiles LIMIT 1')
            except sqlite3.Error:
                raise MBTilesTileStorageError('Invalid table')
            else:
                self._is_mbtiles = True
        else:
            self._is_mbtiles = False

        # For standard Mbtiles file, use database mtime as Tile mtime
        if self._is_mbtiles:
            self._mtime = os.stat(self._database).st_mtime
        else:
            self._mtime = 0

        # Close and reset the connection
        self._conn.close()
        self._conn = None

    def _get_conn(self):
        # NOTE: This is necessary because sqlite3 is not thread safe, and
        #       connection object can only be used in the thread it was
        #       created.  To solve this we use TLS and lazy creation
        if self._conn is None:
            self._conn = sqlite3.connect(self._database, timeout=self._timeout)
        return self._conn

    def _make_mbtiles_index(self, tile_index):
        # Mbtiles has reversed y-axis, which differs with every other format...
        z, x, y = tile_index.coord
        return z, x, 2 ** z - y - 1

    def _make_metadata(self, metadata):
        metadata = dict((k, v) for (k, v) in metadata.iteritems() \
                        if k not in['ext', 'mimetype'])
        return json.dumps(metadata)

    def get(self, tile_index):
        z, x, y = self._make_mbtiles_index(tile_index)
        conn = self._get_conn()
        with conn:
            if self._is_mbtiles:
                cur = conn.execute('''
                    SELECT tile_data FROM tiles
                    WHERE zoom_level=? AND tile_column=? AND tile_row=?
                    ''',
                    (z, x, y))
                row = cur.fetchone()
                if row is None:
                    return None

                data = row[0]
                metadata = dict(ext=self._ext,
                                mimetype=self._mimetype,
                                mtime=self._mtime)

            else:
                cur = conn.execute('''
                    SELECT tile_data, metadata FROM tiles
                    WHERE zoom_level=? AND tile_column=? AND tile_row=?
                    ''',
                    (z, x, y))
                row = cur.fetchone()
                if row is None:
                    return None

                data, metadata = row[0], row[1]

                data = str(data)
                metadata = json.loads(str(row[1]))
                metadata['ext'] = self._ext
                metadata['mimetype'] = self._mimetype

            return Tile(tile_index, data, metadata)

    def put(self, tile):
        z, x, y = self._make_mbtiles_index(tile.index)

        if 'ext' in tile.metadata:
            assert tile.metadata['ext'] == self._ext

        if self._is_mbtiles:
             raise MBTilesTileStorageError("Don't support write to standard Mbtiles")

        tile_hash = tile.datahash
        data = buffer(tile.data)
        metadata = buffer(self._make_metadata(tile.metadata))

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
                tileindex(z, x, y, tilehash, metadata)
                VALUES (?, ?, ?, ?, ?)''',
                (z, x, y, tile_hash, metadata))

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
                metadata = self._make_metadata(tile.metadata)
                yield z, x, y, hash, buffer(tile.data), buffer(metadata)

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
                tileindex(z, x, y, tilehash, metadata)
                VALUES (?, ?, ?, ?, ?)''',
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
