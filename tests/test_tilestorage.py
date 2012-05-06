'''
Created on May 3, 2012

@author: Kotaimen
'''
import os, os.path
import shutil
import time
import unittest
import warnings

from mason.tilestorage import create_tilestorage
from mason.tilelib import Pyramid


class TileStorageTestMixin(object):

    def testGetPut(self):
        tile1 = self.pyramid.create_tile(3, 4, 5, b'tile1', {})
        self.storage.put(tile1)

        tileindex1 = self.pyramid.create_tile_index(3, 4, 5)
        tileindex2 = self.pyramid.create_tile_index(3, 4, 6)
        self.assertTrue(self.storage.get(tileindex1) is not None)
        self.assertTrue(self.storage.get(tileindex2) is None)

        tile3 = self.storage.get(tileindex1)

        self.assertEqual(tile1.index, tile3.index)
        self.assertEqual(tile1.data, tile3.data)
#        self.assertEqual(tile3.metadata['ext'], 'txt')
#        self.assertEqual(tile3.metadata['mimetype'], 'text/plain')
#        self.assertTrue(time.time() -
#                        tile3.metadata['mtime'] < 1,
#                        "it really should'nt take so long"
#                        )

        self.assertTrue(self.storage.has(tileindex1))
        self.storage.delete(tileindex1)
        self.assertFalse(self.storage.has(tileindex1))

    def testGetPutMulti(self):
        tile1 = self.pyramid.create_tile(4, 5, 6, b'tile1', {})
        tile2 = self.pyramid.create_tile(4, 5, 7, b'tile2', {})
        tile3 = self.pyramid.create_tile(4, 5, 8, b'tile3', {})

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
                                                     tileindex4]), {})

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
        self.pyramid = Pyramid(levels=list(xrange(0, 21)))
        self.output_dir = os.path.join('output', 'test_fsstorage1')
        if os.path.exists(self.output_dir):
            shutil.rmtree('test_fsstorage1', ignore_errors=True)

        self.storage = create_tilestorage('filesystem',
                                          'teststorage',
                                          root=self.output_dir,
                                          ext='txt',
                                          compress=False
                                          )

    def tearDown(self):
        self.storage.flush_all()

    def testFilename(self):
        tile1 = self.pyramid.create_tile(0, 0, 0, b'tile1', {})
        self.storage.put(tile1)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir,
                                                    '00',
                                                    '0-0-0.txt')))

        tile2 = self.pyramid.create_tile(20, 1000, 2000, b'tile2', {})
        self.storage.put(tile2)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir,
                                                    '20',
                                                    '00', '07', 'C0', '0F',
                                                    '20-1000-2000.txt')))


class TestFileSystemTileStorageCompressed(TileStorageTestMixin, unittest.TestCase):

    def setUp(self):
        self.pyramid = Pyramid(levels=list(xrange(0, 21)))
        self.output_dir = os.path.join('output', 'test_fsstorage2')
        if os.path.exists(self.output_dir):
            shutil.rmtree('test_fsstorage2', ignore_errors=True)

        self.storage = create_tilestorage('filesystem',
                                          'teststorage',
                                          root=self.output_dir,
                                          ext='txt',
                                          mimetype='text/plain',
                                          compress=True
                                          )

    def tearDown(self):
        self.storage.flush_all()

    def testFilename(self):
        tile1 = self.pyramid.create_tile(0, 0, 0, b'tile1', {})
        self.storage.put(tile1)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir,
                                                    '00',
                                                    '0-0-0.txt.gz')))

        tile2 = self.pyramid.create_tile(20, 1000, 2000, b'tile2', {})
        self.storage.put(tile2)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir,
                                                    '20',
                                                    '00', '07', 'C0', '0F',
                                                    '20-1000-2000.txt.gz')))


class TestMemcacheStorageDefault(TileStorageTestMixin, unittest.TestCase):

    def setUp(self):
        warnings.warn('memcache storage test flushes everything in localhost:11211')
        self.pyramid = Pyramid(levels=list(xrange(0, 21)))
        self.output_dir = os.path.join('output', 'test_fsstorage2')

        self.storage = create_tilestorage('memcache',
                                          'teststorage',
                                          servers=['localhost:11211'],
                                          )

    def tearDown(self):
        self.storage.flush_all()


class TestMemcacheStorageCompressed(TileStorageTestMixin, unittest.TestCase):

    def setUp(self):
        warnings.warn('memcache storage test flushes everything in localhost:11211')
        self.pyramid = Pyramid(levels=list(xrange(0, 21)))
        self.output_dir = os.path.join('output', 'test_fsstorage2')

        self.storage = create_tilestorage('memcache',
                                          'teststorage',
                                          servers=['localhost:11211'],
                                          compress=True
                                          )

    def tearDown(self):
        self.storage.flush_all()

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
