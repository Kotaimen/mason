#!/usr/bin/env python
# -*- encoding: utf8 -*-

'''
Created on Jun 2, 2012

@author: Kotaimen
'''

import re
import os
import shutil
import argparse
import threading
import Queue
import copy
import multiprocessing
import subprocess
import pprint
import logging

logger = logging.getLogger('transtorage')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
#handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(handler)

from mason.tilestorage import create_tilestorage, attach_tilestorage
from mason.core import Format, Tile

#===============================================================================
# Converters
#===============================================================================


class TileConverter(object):

    """ Convert tile format, by default, simply do copying """

    def __init__(self):
        self.format = Format.ANY

    def convert(self, input):
        return self.do_convert(input)

    def do_convert(self, input):
        return input


class JPEGTileConverter(TileConverter):

    """ Convert to JPEG image using imagemagick """

    def __init__(self, quality=0.75):
        TileConverter.__init__(self)
        self.quality = quality
        self.format = Format.JPG

    def do_convert(self, input):
        args = ['convert', '-',
                '-quality', '%.0f%%' % (self.quality * 100),
                'jpg:-']
        popen = subprocess.Popen(args,
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        stdout, stderr = popen.communicate(input)
        retcode = popen.poll()
        if retcode != 0:
            raise subprocess.CalledProcessError(retcode, args, stderr)
        return stdout


class PNGTileConverter(TileConverter):

    """ Convert to PNG image using imagemagick """

    def __init__(self, colors=0):
        TileConverter.__init__(self)
        self.colors = colors
        self.format = Format.JPG

    def do_convert(self, input):
        args = ['convert', '-', ]
        if self.colors > 0:
            args.extend(['-colors', self.colors])
        args.append('png:-')
        popen = subprocess.Popen(args,
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        stdout, stderr = popen.communicate(input)
        retcode = popen.poll()
        if retcode != 0:
            raise subprocess.CalledProcessError(retcode, args, stderr)
        return stdout

#===============================================================================
# Transformer
#===============================================================================


class StorageTransformer(object):

    def __init__(self,
                 input_pathname,
                 output_pathname,
                 converter=None,
                 poolsize=2,
                 overwrite=False,
                 ):
        logger.info('creating storages...')
        self._input_pathname = input_pathname
        self._output_pathname = output_pathname
        if converter is None:
            self._converter = TileConverter()
        else:
            self._converter = converter
        self._pyramid = None
        self._metadata = None
        self._input_storage = None
        self._output_storage = None
        self._create_input_storage(converter)
        self._create_output_storage(overwrite)

        self._pool = list()
        self._queue = Queue.Queue(maxsize=1024)
        logger.info('starting transforming worker thread...')
        for i in range(poolsize):
            thread = threading.Thread(target=self.worker)
            thread.daemon = True
            thread.start()
            self._pool.append(thread)

    def translate(self):
        for (z, x, y), image_filename in self._walk_storage():
            try:
                tile_index = self._pyramid.create_tile_index(z, x, y)
            except Exception: # TileOutOfRange
                pass
            self._queue.put((tile_index, image_filename))

        self._queue.join()
        self._output_storage.close()
        logger.info('...done')

    def worker(self):
        while True:
            task = self._queue.get()
            try:
                (tile_index, image_filename) = task
                with open(image_filename, 'rb') as fp:
                    input_data = fp.read()
                    tile_data = self._converter.convert(input_data)
                    before_size = len(input_data)
                    after_size = len(tile_data)
                    logger.debug('convert %s (%.2fk->%.2fk@%.1f%%)',
                                 tile_index.coord,
                                 before_size / 1024.,
                                 after_size / 1024.,
                                 after_size * 100. / before_size)

                tile = Tile.from_tile_index(tile_index, tile_data)
                self._output_storage.put(tile)
            finally:
                self._queue.task_done()

    def _create_input_storage(self, converter):
        raise NotImplementedError

    def _create_output_storage(self, overwrite):
        raise NotImplementedError

    def _walk_storage(self):
        raise NotImplementedError


class FS2MbtilesStorageTransformer(StorageTransformer):

    def _create_input_storage(self, converter):
        self._input_storage = attach_tilestorage('filesystem',
                                                 root=self._input_pathname)
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
                logger.info('deleting %s...', self._output_pathname)
                os.remove(self._output_pathname)
            else:
                raise RuntimeError('"%s" already exists' % self._output_pathname)
        logger.debug('pyramid:')
        logger.debug(self._pyramid.summarize())
        logger.debug('metadata:')
        logger.debug(tuple(self._metadata))
        self._output_storage = create_tilestorage('mbtilesbw',
                                                  pyramid=self._pyramid,
                                                  metadata=self._metadata,
                                                  database=self._output_pathname,)

    def _walk_storage(self):
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


class FS2SimpleStorageTransformer(FS2MbtilesStorageTransformer):

    def _create_output_storage(self, overwrite):
        if os.path.exists(self._output_pathname):
            if overwrite:
                logger.info('deleting... %s', self._output_pathname)
                shutil.rmtree(self._output_pathname)
            else:
                raise RuntimeError('"%s" already exists' % self._output_pathname)
        logger.debug('pyramid:')
        logger.debug(self._pyramid.summarize())
        logger.debug('metadata:')
        logger.debug(tuple(self._metadata))
        self._output_storage = create_tilestorage('filesystem',
                                                  pyramid=self._pyramid,
                                                  metadata=self._metadata,
                                                  root=self._output_pathname,
                                                  simple=True,
                                                  compress=False,)


def parse_args():
    parser = argparse.ArgumentParser(description='Transform tile storages',
                                     epilog=\
                                     ''' Convert between different tile storages for publishing.
                                     ''',
                                     usage='%(prog)s INPUT_STORAGE OUTPUT_STORAGE [OPTIONS]',
                                     )

    parser.add_argument('-m', '-mode',
                        dest='mode',
                        choices=['fs2mbtiles', 'fs2simple',
                                 #'fission', 
                                ],
                        required=True,
                        help='''Specify operation mode, available choices are:
                        %(choices)s. fs2mbiles: convert a filesystem tile storage
                        to a mbtiles tile storage.''',)

    parser.add_argument(dest='input_dirname',
                        metavar='INPUT_STORAGE',
                        help='''Input tile storage path, must be a non
                        simple file system storage
                        ''',)

    parser.add_argument(dest='output_dirname',
                        metavar='OUPUT_STORAGE',
                        help='''Output tile storage path,
                        can be a directory name (file system)
                        or filename (mbtiles)
                        ''',)

    parser.add_argument('-f', '--format',
                        dest='format',
                        default='as-is',
                        choices=['as-is', 'jpg', ],
                        help='''Output image format, default is don't
                        change image format (as-is)''',)

    parser.add_argument('-c', '--compression',
                        type=float,
                        dest='compression',
                        default=0.75,
                        help='''JPEG compression level, default is %(default)s,
                        reasonable value is 0.6~0.9''',)

    parser.add_argument('-o', '--overwrite',
                        dest='overwrite',
                        action='store_true',
                        default=False,
                        help='''Overwrites existing storage, otherwise
                        transform will fail if target already exists''',)

    parser.add_argument('-q', '--quiet',
                        dest='quiet',
                        action='store_true',
                        default=False,
                        help='''Be quiet, don't complain unless there
                        are errors''',)

    parser.add_argument('-w', '--workers',
                        type=int,
                        dest='workers',
                        default=multiprocessing.cpu_count(),
                        help='''Number of concurrent workers, default is
                        %(default)s''',)

    return parser.parse_args()


def main():
    options = parse_args()
#    print options

    if options.format == 'jpg':
        converter = JPEGTileConverter(quality=options.compression)
    else:
        converter = None
    if options.mode == 'fs2mbtiles':
        transformer_class = FS2MbtilesStorageTransformer
    elif options.mode == 'fs2simple':
        transformer_class = FS2SimpleStorageTransformer

    transformer = transformer_class(options.input_dirname,
                                    options.output_dirname,
                                    converter=converter,
                                    poolsize=options.workers,
                                    overwrite=options.overwrite)

    transformer.translate()

if __name__ == '__main__':
    main()
