'''
Created on May 3, 2012

@author: Kotaimen
'''
import os, os.path
import sys
import shutil
import time
import unittest
import warnings
import threading
import memcache

from mason.tilestorage import TileStorageFactory, MBTilesTileStorage
from mason.core import Format, Metadata, Pyramid, Tile, MetaTile
from mason.tilestorage.cluster import TileCluster

# Tile storage factory
factory = TileStorageFactory()


class TileStorageTestMixin(object):

    def testGetPut(self):
        tile1 = self.pyramid.create_tile(3, 4, 5, b'tile1')
        self.storage.put(tile1)

        tileindex1 = self.pyramid.create_tile_index(3, 4, 5)
        tileindex2 = self.pyramid.create_tile_index(3, 4, 6)
        self.assertTrue(self.storage.get(tileindex1) is not None)
        self.assertTrue(self.storage.get(tileindex2) is None)

        tile3 = self.storage.get(tileindex1)

        self.assertTrue(tile3 is not None)

        self.assertEqual(tile1.index, tile3.index)
        self.assertEqual(tile1.data, tile3.data)

        self.assertTrue(self.storage.has(tileindex1))
        self.storage.delete(tileindex1)
        self.assertFalse(self.storage.has(tileindex1))

    def testGetPutMulti(self):
        tile1 = self.pyramid.create_tile(4, 5, 6, b'tile1')
        tile2 = self.pyramid.create_tile(4, 5, 7, b'tile2')
        tile3 = self.pyramid.create_tile(4, 5, 8, b'tile3')

        self.storage.put_multi([tile1, tile2, tile3])

        tileindex1 = self.pyramid.create_tile_index(4, 5, 6)
        tileindex2 = self.pyramid.create_tile_index(4, 5, 7)
        tileindex3 = self.pyramid.create_tile_index(4, 5, 9)
        tileindex4 = self.pyramid.create_tile_index(4, 5, 10)

        tiles1 = self.storage.get_multi([tileindex1, tileindex2])

        self.assertSetEqual(set(tiles1.keys()),
                            set([tileindex1, tileindex2]))
        self.assertEqual(tiles1[tileindex1].data, tile1.data)
        self.assertDictEqual(self.storage.get_multi([tileindex3,
                                                     tileindex4])
                             , {})

        tiles2 = self.storage.get_multi([tileindex1, tileindex2,
                                         tileindex3])

        self.assertSetEqual(set(tiles2.keys()),
                            set([tileindex1, tileindex2]))

        self.assertTrue(self.storage.has_all([tileindex1, tileindex2]))
        self.assertFalse(self.storage.has_all([tileindex1, tileindex4]))
        self.assertTrue(self.storage.has_any([tileindex1, tileindex4]))
        self.storage.delete_multi([tileindex1, tileindex3, tileindex4])
        self.assertTrue(self.storage.has_any([tileindex1, tileindex2]))
        self.assertFalse(self.storage.has_any([tileindex1, tileindex3]))


class TestFileSystemTileStorageDefault(TileStorageTestMixin, unittest.TestCase):

    def setUp(self):
        self.pyramid = Pyramid(levels=range(21), format=Format.DATA)
        self.metadata = Metadata.make_metadata(tag='TestFileSystemTileStorageDefault',
                                               version='1.0.0.0.0.0')
        self.output_dir = os.path.join('output', 'TestFileSystemTileStorageDefault')

        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir, ignore_errors=True)

        self.storage = factory('filesystem',
                               self.pyramid,
                               self.metadata,
                               root=self.output_dir,
                               compress=False,
                               simple=False,)

    def tearDown(self):
#        self.storage.flush_all()
        self.storage.close()

    def testFilename(self):
        tile1 = self.pyramid.create_tile(0, 0, 0, b'tile1', {})
        self.storage.put(tile1)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir,
                                                    '00',
                                                    '0-0-0.dat')))

        tile2 = self.pyramid.create_tile(20, 1000, 2000, b'tile2', {})
        self.storage.put(tile2)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir,
                                                    '20',
                                                    '00', '07', 'C0', '0F',
                                                    '20-1000-2000.dat')))


class TestFileSystemTileStorageCompressed(TileStorageTestMixin, unittest.TestCase):

    def setUp(self):
        self.pyramid = Pyramid(levels=range(21), format=Format.DATA)
        self.metadata = Metadata.make_metadata(tag='TestFileSystemTileStorageCompressed',
                                               version='1.0.0.0.0.0')
        self.output_dir = os.path.join('output', 'TestFileSystemTileStorageCompressed')

        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir, ignore_errors=True)

        self.storage = factory('filesystem',
                               self.pyramid,
                               self.metadata,
                               root=self.output_dir,
                               compress=True,
                               simple=False,)

    def tearDown(self):
#        self.storage.flush_all()
        self.storage.close()

    def testFilename(self):
        tile1 = self.pyramid.create_tile(0, 0, 0, b'tile1', {})
        self.storage.put(tile1)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir,
                                                    '00',
                                                    '0-0-0.dat.gz')))

        tile2 = self.pyramid.create_tile(20, 1000, 2000, b'tile2', {})
        self.storage.put(tile2)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir,
                                                    '20',
                                                    '00', '07', 'C0', '0F',
                                                    '20-1000-2000.dat.gz')))


class TestFileSystemTileStorageSimpleCompressed(TileStorageTestMixin, unittest.TestCase):

    def setUp(self):
        self.pyramid = Pyramid(levels=range(21), format=Format.DATA)
        self.metadata = Metadata.make_metadata(tag='TestFileSystemTileStorageSimpleCompressed',
                                               version='1.0.0.0.0.0')
        self.output_dir = os.path.join('output', 'TestFileSystemTileStorageSimpleCompressed')

        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir, ignore_errors=True)

        self.storage = factory('filesystem',
                               self.pyramid,
                               self.metadata,
                               root=self.output_dir,
                               compress=False,
                               simple=True,)

    def tearDown(self):
#        self.storage.flush_all()
        self.storage.close()


class TestMemcachedTileStorage(TileStorageTestMixin, unittest.TestCase):

    def setUp(self):
        self.pyramid = Pyramid(levels=range(21), format=Format.DATA)
        self.metadata = Metadata.make_metadata(tag='TestMemcachedTileStorage')

        self.storage = factory('memcache',
                               self.pyramid,
                               self.metadata)

    def tearDown(self):
#        self.storage.flush_all()
        self.storage.close()


class TestMBTilesTileStorage(TileStorageTestMixin, unittest.TestCase):

    def setUp(self):
        self.pyramid = Pyramid(levels=range(21), format=Format.DATA)

        self.metadata = Metadata.make_metadata(tag='TestMBTilesTileStorage',
                                               version='1',
                                               attribution='foo')

        filename = './output/TestMBTilesTileStorage.db'
        if os.path.exists(filename):
            os.unlink(filename)
        self.storage = factory('mbtiles',
                               self.pyramid,
                               self.metadata,
                               database=filename)

    def tearDown(self):
        tile1 = self.pyramid.create_tile(3, 4, 5, b'tile1')
        self.storage.put(tile1)
        storage = MBTilesTileStorage.from_mbtiles('./output/TestMBTilesTileStorage.db')
        self.assertEqual(storage.metadata.version, self.storage.metadata.version)
        self.storage.close()


class TestMBTilesTileStorageBackgroundWriter(unittest.TestCase):

    def setUp(self):
        self.pyramid = Pyramid(levels=range(21), format=Format.DATA)

        self.metadata = Metadata.make_metadata(tag='TestMBTilesTileStorageBackgroundWriter',)
        filename = './output/TestMBTilesTileStorageBackgroundWriter.db'
        if os.path.exists(filename):
            os.unlink(filename)
        self.storage = factory('mbtilesbw',
                               self.pyramid,
                               self.metadata,
                               database=filename)

    def tearDown(self):
#        self.storage.flush_all()
        self.storage.close()

    def testGetPut(self):
        tile1 = self.pyramid.create_tile(3, 4, 5, b'tile1')
        self.storage.put(tile1)
        self.storage.sync()
        tileindex1 = self.pyramid.create_tile_index(3, 4, 5)
        tileindex2 = self.pyramid.create_tile_index(3, 4, 6)
        self.assertTrue(self.storage.get(tileindex1) is not None)
        self.assertTrue(self.storage.get(tileindex2) is None)

        tile3 = self.storage.get(tileindex1)

        self.assertEqual(tile1.index, tile3.index)
        self.assertEqual(tile1.data, tile3.data)

        self.assertTrue(self.storage.has(tileindex1))
        self.storage.delete(tileindex1)
        self.storage.sync()
        self.assertFalse(self.storage.has(tileindex1))

    def testGetPutMulti(self):
        tile1 = self.pyramid.create_tile(4, 5, 6, b'tile1')
        tile2 = self.pyramid.create_tile(4, 5, 7, b'tile2')
        tile3 = self.pyramid.create_tile(4, 5, 8, b'tile3')

        self.storage.put_multi([tile1, tile2, tile3])
        self.storage.sync()

        tileindex1 = self.pyramid.create_tile_index(4, 5, 6)
        tileindex2 = self.pyramid.create_tile_index(4, 5, 7)
        tileindex3 = self.pyramid.create_tile_index(4, 5, 9)
        tileindex4 = self.pyramid.create_tile_index(4, 5, 10)

        tiles1 = self.storage.get_multi([tileindex1, tileindex2])

        self.assertSetEqual(set(tiles1.keys()),
                            set([tileindex1, tileindex2]))
        self.assertEqual(tiles1[tileindex1].data, tile1.data)
        self.assertDictEqual(self.storage.get_multi([tileindex3,
                                                     tileindex4])
                             , {})

        tiles2 = self.storage.get_multi([tileindex1, tileindex2,
                                         tileindex3])

        self.assertSetEqual(set(tiles2.keys()),
                            set([tileindex1, tileindex2]))

        self.assertTrue(self.storage.has_all([tileindex1, tileindex2]))
        self.assertFalse(self.storage.has_all([tileindex1, tileindex4]))
        self.assertTrue(self.storage.has_any([tileindex1, tileindex4]))
        self.storage.delete_multi([tileindex1, tileindex3, tileindex4])
        self.storage.sync()
        self.assertTrue(self.storage.has_any([tileindex1, tileindex2]))
        self.assertFalse(self.storage.has_any([tileindex1, tileindex3]))


class TestCascadeTileStorage(TileStorageTestMixin, unittest.TestCase):

    def setUp(self):
        self.pyramid = Pyramid(levels=range(21), format=Format.DATA)
        self.metadata = Metadata.make_metadata(tag='TestCascadeTileStorage')
        self.output_dir = os.path.join('output', 'TestCascadeTileStorage')

        self.storage = factory('cascade',
                               self.pyramid,
                               self.metadata,
                               violate=['memcache', {'servers': ['localhost:11211', ]}],
                               presistent=['filesystem', {'root': self.output_dir}],
                               )

    def tearDown(self):
        self.storage.close()


class TestS3TileStorage(TileStorageTestMixin, unittest.TestCase):

    def setUp(self):
        self.pyramid = Pyramid(levels=range(21), format=Format.DATA)
        self.metadata = Metadata.make_metadata(tag='S3StorageTest')
        self.storage = factory('s3',
                               self.pyramid,
                               self.metadata,
                               access_key=None,
                               secret_key=None,
                               bucket_name='tilestorage',
                               simple=False,
#                               tag_name='foobar'
                               )

    def tearDown(self):
        self.storage.close()


class TestMetaTileCache(unittest.TestCase):

    def setUp(self):
        self.pyramid = Pyramid(levels=range(21), format=Format.DATA)
        self.metadata = Metadata.make_metadata(tag='TestMetaTileCache',
                                               version='1.0.0.0.0.0')
        self.output_dir = os.path.join('output', 'TestMetaTileCache')

        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir, ignore_errors=True)

        self.storage = factory('metacache',
                               self.pyramid,
                               self.metadata,
                               root=self.output_dir,
                               )

    def tearDown(self):
#        self.storage.flush_all()
        self.storage.close()

    def testGetPut(self):
        tile1 = self.pyramid.create_metatile(3, 4, 5, 4, b'tile1')
        self.storage.put(tile1)

        tileindex1 = self.pyramid.create_metatile_index(3, 4, 5, 4)
        tileindex2 = self.pyramid.create_metatile_index(3, 3, 6, 4)
        self.assertTrue(self.storage.get(tileindex1) is not None)
        self.assertTrue(self.storage.get(tileindex2) is None)

        tile3 = self.storage.get(tileindex1)

        self.assertEqual(tile1.index, tile3.index)
        self.assertEqual(tile1.data, tile3.data)

        self.assertTrue(self.storage.has(tileindex1))
        self.storage.delete(tileindex1)
        self.assertFalse(self.storage.has(tileindex1))


class TestTileCluster(unittest.TestCase):

    def setUp(self):
        self.pyramid = Pyramid(levels=range(21), format=Format.DATA)

    def testFusion(self):
        tiles = [self.pyramid.create_tile(4, 0, 0, b'tile1'),
                 self.pyramid.create_tile(4, 1, 0, b'tile2'),
                 self.pyramid.create_tile(4, 0, 1, b'tile2'),
                 self.pyramid.create_tile(4, 1, 1, b'tile4'), ]

        cluster = TileCluster(self.pyramid, tiles)

        zip_file = cluster.fusion()

        with open(os.path.join('output', 'clustertest1.zip'), 'wb') as fp:
            fp.write(zip_file)

        tiles_readback = cluster.fission(self.pyramid, zip_file)

        self.assertEqual(set(t.index.coord for t in tiles),
                         set(t.index.coord for t in tiles_readback))

        self.assertEqual(set(t.data_hash for t in tiles),
                         set(t.data_hash for t in tiles_readback))


class TestFileClusterStorage(TileStorageTestMixin, unittest.TestCase):

    def setUp(self):
        self.pyramid = Pyramid(levels=range(21), format=Format.DATA)
        self.metadata = Metadata.make_metadata(tag='TestClusterStorage',
                                               version='1.0.0.0.0.0')
        self.output_dir = os.path.join('output', 'TestClusterStorage')

        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir, ignore_errors=True)

        self.storage = factory('cluster',
                               self.pyramid,
                               self.metadata,
                               stride=2,
                               servers=['localhost:11211'],
                               timeout=0,
                               root=self.output_dir,
                               compress=False,)

    def tearDown(self):
#        self.storage.flush_all()
        self.storage.close()

    def testGetPutMulti(self):
        tiles = [self.pyramid.create_tile(4, 0, 0, b'tile1'),
                 self.pyramid.create_tile(4, 1, 0, b'tile2'),
                 self.pyramid.create_tile(4, 0, 1, b'tile3'),
                 self.pyramid.create_tile(4, 1, 1, b'tile2'), ]

        self.storage.put_multi(tiles)

        tileindex1 = self.pyramid.create_tile_index(4, 0, 1)
        tileindex2 = self.pyramid.create_tile_index(4, 1, 1)

        tile1 = self.storage.get(tileindex1)
        self.assertEqual(tile1.data, b'tile3')

        tile2 = self.storage.get(tileindex2)
        self.assertEqual(tile2.data, b'tile2')


class TestS3ClusterStorage(TestFileClusterStorage):

    def setUp(self):
        self.pyramid = Pyramid(levels=range(21), format=Format.DATA)
        self.metadata = Metadata.make_metadata(tag='S3ClusterStorageTest',
                                               version='2.0')

        self.storage = factory('s3cluster',
                               self.pyramid,
                               self.metadata,
                               stride=2,
                               servers=['localhost:11211'],
                               timeout=0,
                               access_key=None,
                               secret_key=None,
                               bucket_name='tilestorage',
                               compress=True,
                               )


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
