#!/usr/bin/env python
# -*- encoding: utf8 -*-

'''
Created on Jun 2, 2012

@author: Kotaimen
'''

import re
import os
import argparse
import threading
import Queue
import copy
import multiprocessing
import subprocess
import pprint
import logging

#logger = logging.getLogger('transtorage')
#logger.setLevel(logging.DEBUG)


from mason.tilestorage import (FileSystemTileStorage,
                               MBTilesTileStorage,
                               MBTilesTileStorageWithBackgroundWriter,)
from mason.core import Format, Tile

#===============================================================================
# Converters
#===============================================================================


class TileConverter(object):

    def __init__(self):
        self.format = Format.ANY

    def convert(self, input_filename):
        with open(input_filename, 'rb') as fp:
            return fp.read()


class JPEGTileConverter(object):

    def __init__(self, quality=0.8):
        self.quality = quality
        self.format = Format.JPEG

    def convert(self, input_filename):
        data = subprocess.check_output(['convert',
                                        input_filename,
                                        '-quality',
                                        '%.0f%%' % (self.quality * 100),
                                        'jpg:-'])
        before_size = os.stat(input_filename).st_size
        after_size = len(data)
#        print 'convert %s to jpg (%.2fk->%.2fk@%.1f%%)' % \
#            (os.path.basename(input_filename),
#             before_size / 1024.,
#             after_size / 1024.,
#             after_size * 100. / before_size)
        return data


#class PNGTileConverter(object):
#
#    def __init__(self, colors=256):
#        self.colors = colors
#        self.format = Format.PNG256
#
#    def convert(self, input_filename):
#        data = subprocess.check_output(['convert',
#                                        input_filename,
#                                        '-quality',
#                                        '%.0f%%' % (self.quality * 100),
#                                        'jpg:-'])
#        before_size = os.stat(input_filename).st_size
#        after_size = len(data)
#        print 'convert %s (%.2fk->%.2fk@%.1f%%)' % \
#            (input_filename,
#             before_size / 1024.,
#             after_size / 1024.,
#             after_size * 100. / before_size)
#        return data

#===============================================================================
# Translators
#===============================================================================

class FS2MBStorageTranslator(object):

    def __init__(self,
                 input_pathname,
                 output_pathname,
                 converter=None,
                 poolsize=2,
                 overwrite=False,
                 ):
        print 'creating storages...'
        self._input_pathname = input_pathname
        self._output_pathname = output_pathname

        self._create_input_storage(converter)
        self._create_output_storage(overwrite)

        self._pool = list()
        self._queue = Queue.Queue(maxsize=1024)
        print 'starting transforming worker thread...'
        for i in range(poolsize):
            thread = threading.Thread(target=self.worker)
            thread.daemon = True
            thread.start()
            self._pool.append(thread)

    def _create_input_storage(self, converter):
        self._input_storage = FileSystemTileStorage.from_config(self._input_pathname)
        self._pyramid = copy.deepcopy(self._input_storage.pyramid)
        self._metadata = copy.deepcopy(self._input_storage.metadata)
        if converter is None:
            self._converter = TileConverter()
        else:
            self._converter = converter
            # HACK: Replace format object of the new Pyramid
            self._pyramid._format = self._converter.format

    def _create_output_storage(self, overwrite):

        if os.path.exists(self._output_pathname):
            if overwrite:
                os.remove(self._output_pathname)
            else:
                raise RuntimeError('"%s" already exists' % self._output_pathname)
        print 'pyramid:'
        pprint.pprint(self._pyramid.summarize())
        print 'metadata:'
        pprint.pprint(tuple(self._metadata))
        self._output_storage = \
            MBTilesTileStorageWithBackgroundWriter(self._pyramid,
                                                   self._metadata,
                                                   self._output_pathname)

    def translate(self):
        for (z, x, y), image_filename in self.walk_storage():
            tile_index = self._pyramid.create_tile_index(z, x, y)
            self._queue.put((tile_index, image_filename))

        self._queue.join()
        self._output_storage.close()
        print '...done'

    def worker(self):
        while True:
            task = self._queue.get()
            try:
                (tile_index, image_filename) = task
                tile_data = self._converter.convert(image_filename)
                tile = Tile.from_tile_index(tile_index, tile_data)
                self._output_storage.put(tile)
            finally:
                self._queue.task_done()

    def walk_storage(self):
        rootdir = self._input_pathname
        ext = self._input_storage.pyramid.format.extension

        for base, dirs, files in os.walk(rootdir):
            for filename in files:
                match = re.match('(\d+)-(\d+)-(\d+)%s' % ext, filename)
                if not match:
                    continue
                z, x, y = tuple(map(int, match.groups()))
                if z not in self._pyramid.levels:
                    continue
                fullname = os.path.join(base, filename)
                yield (z, x, y), fullname


def parse_args():
    parser = argparse.ArgumentParser(description='Tranform between tile storages',
                                     usage='%(prog)s INPUT_STORAGE OUTPUT_STORAGE [OPTIONS]',
                                     )

    parser.add_argument('-m', '-mode',
                        dest='mode',
                        choices=['fs2mbtiles', 'fs2simple'],
                        default='fs2mbtiles',
                        required=True,
                        help='''Specify operation mode available choices are:
                        %(choices)s, default is %(default)s''',)

    parser.add_argument(dest='input_dirname',
                        metavar='INPUT_STORAGE',
                        help='''Input tile storage path, must be a non
                        simple filesystem storage
                        ''',)

    parser.add_argument(dest='output_dirname',
                        metavar='OUPUT_STORAGE',
                        help='''Output tile storage path, depends on which mode,
                        can bea directory name or filename
                        ''',)

    parser.add_argument('-f', '--format',
                        dest='format',
                        default='as-is',
                        choices=['as-is', 'jpg', ],
                        help='''Output image format, default is don't change
                        image format''',)

    parser.add_argument('-c', '--compression',
                        type=float,
                        dest='compression',
                        default=0.6,
                        help='''JPEG compression level, default is %(default)s''',)

    parser.add_argument('-o', '--overwrite',
                        dest='overwrite',
                        action='store_true',
                        default=False,
                        help='''Overwrites existing storage''',)

    parser.add_argument('-w', '--workers',
                        type=int,
                        dest='workers',
                        default=multiprocessing.cpu_count(),
                        help='''Number of concurrent workers, default is
                        %(default)s''',)

    return parser.parse_args()


def main():
    options = parse_args()
    print options

    if options.format == 'jpg':
        converter = JPEGTileConverter(quality=options.compression)
    else:
        converter = None

    translator = FS2MBStorageTranslator(options.input_dirname,
                                        options.output_dirname,
                                        converter=converter,
                                        poolsize=options.workers,
                                        overwrite=options.overwrite)

    translator.translate()

if __name__ == '__main__':
    main()
