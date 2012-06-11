#!/usr/bin/env python

""" Generate upper level tiles by scaling down lower level tiles (aka uplifting)

This script requires ImageMagick and bypasses most TileStorage internals.

Created on May 18, 2012
@author: kotaimen

"""

import os, os.path
import re
import subprocess
import logging
import multiprocessing
import threading
import argparse

from mason.utils import Timer
from mason.core import tile_coordiante_to_dirname


def gen_tasks_for_complex_storage(root, level, ext, default):
    level_root = os.path.join(root, '%02d' % level)
    pattern = re.compile(r'(\d+)-(\d+)-(\d+)\.' + ext)

    print 'Checking tiles in "%s"...' % level_root

    target_tiles = dict()

    def tile_path(z, x, y):
        dirs = os.path.join(*tile_coordiante_to_dirname(z, x, y))
        basename = '%d-%d-%d.%s' % (z, x, y, ext)
        return os.path.join(root, dirs, basename)

    for base, dirs, files in os.walk(level_root):
        for filename in files:
            match = pattern.match(filename)
            if not match:
                continue
            z, x, y = tuple(map(int, match.groups()))

            key = z - 1, x // 2, y // 2
            if key not in target_tiles:
                target_tiles[key] = 1
            else:
                target_tiles[key] += 1

    print '%d tiles can be uplifted.' % len(target_tiles)

    for (z, x, y), n in target_tiles.iteritems():

        if not default and n < 4:
            print 'Cannot uplift %d/%d/%d ' % (z, x, y)
            continue

        input_names = [tile_path(z + 1, x * 2, y * 2),
                       tile_path(z + 1, x * 2 + 1, y * 2),
                       tile_path(z + 1, x * 2, y * 2 + 1),
                       tile_path(z + 1, x * 2 + 1, y * 2 + 1)]

        output_name = tile_path(z, x, y)

        for n in range(len(input_names)):
            if not os.path.exists(input_names[n]):
                if default:
                    input_names[n] = default
                else:
                    continue

        yield input_names, output_name, ext


def process_task(input_names, output_name, ext, sharpen):

    output_dir = os.path.dirname(output_name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    prefix = 'upllift_%d_' % multiprocessing.current_process().ident

    link_names = [os.path.join(output_dir, prefix + '00.' + ext),
                  os.path.join(output_dir, prefix + '10.' + ext),
                  os.path.join(output_dir, prefix + '01.' + ext),
                  os.path.join(output_dir, prefix + '11.' + ext), ]

    for input_name, link_name in zip(input_names, link_names):
        if os.path.exists(link_name):
            os.unlink(link_name)
        try:
            os.link(input_name, os.path.join(output_dir, link_name))
        except OSError:
            print input_name
            raise

    args = ['montage',
            '-quiet',
            '-limit', 'thread', '1',
            '-mode', 'concatenate', '-tile', '2x2',
            ]

    args.extend(link_names)
    args.extend(['-interpolate', 'bicubic', '-resize', '50%'])
    if sharpen > 0:
        args.extend(['-unsharp', str(sharpen)])
    elif sharpen < 0:
        args.extend(['-blur', str(-sharpen)])
    args.append(output_name)
#    print ' '.join(args)
    try:
        with Timer('Uplifted %s in %%(time)s' % os.path.basename(output_name)):
            subprocess.check_call(args, cwd=output_dir)
    finally:
        for link_name in link_names:
            os.unlink(link_name)


def parse_args():
    parser = argparse.ArgumentParser(description=''' Generate upper level tiles
                                     by scaling down lower level tiles''',
                                     epilog=\
'''Very useful for GDAL rendered tiles since render higher levels is very slow.
Note this script only supports uncompressed FileSystemTileCache.
''',
                                     usage='%(prog)s [OPTIONS]',
                                     )

    parser.add_argument('-r', '--root',
                        dest='root',
                        help='''Root directory of the the filesystem
                        tile storage''',
                        metavar='FILE',
                        )

    parser.add_argument('-e', '--ext',
                        dest='ext',
                        choices=['png', 'tif'],
                        help='''Filename extension of the filesystem
                        storage ''',
                        )

    parser.add_argument('-d', '--default',
                        dest='default',
                        default='',
                        help='''Default transparent image if the adjacent tile
                        is missing, if ignored, tiles without adjacent tiles
                        will not be uplifted''',
                        metavar='FILE',
                        )

#    parser.add_argument('-s', '--simple',
#                        dest='simple',
#                        default=False,
#                        action='store_true',
#                        help='''Whether the directory tree is "simple",
#                        which tile is stored as z/x/y.ext, default
#                        is False ''',
#                        )

    parser.add_argument('-v', '--level',
                        dest='level',
                        type=int,
                        help='''Tile level to uplift ''',
                        )

    parser.add_argument('-o', '--overwrite',
                        dest='overwrite',
                        default=False,
                        action='store_true',
                        help='''Overwrite existing tiles''',
                        )

    parser.add_argument('--sharpen',
                        dest='sharpen',
                        default=0.0,
                        type=float,
                        help='''Apply sharpen after resampling, default is 0,
                        means no sharpening'''
                        )

    parser.add_argument('-w', '--workers',
                       dest='workers',
                       default=1,
                       type=int,
                       help='''number of worker processes, default is 1
                       ''',
                       )

    options = parser.parse_args()

    if options.default:
        assert os.path.exists(options.default)

    assert options.ext
    assert options.root

    options.root = os.path.abspath(options.root)

    return options


import prodconsq


class TestTask(object):

    def __init__(self, args):
        self.args = args


class Producer(prodconsq.Producer):

    def __init__(self, tasks):
        self.tasks = tasks

    def items(self):
        for task in self.tasks:
            yield task


class Consumer(prodconsq.Consumer):

    def consume(self, task):
        process_task(*task)


def main():
    options = parse_args()
    tasks = list()
    for input, output, ext in gen_tasks_for_complex_storage(options.root,
                                                            options.level,
                                                            options.ext,
                                                            options.default):

        if os.path.exists(output) and (not options.overwrite):
            continue
        if options.workers == 1:
            process_task(input, output, ext, options.sharpen)
        else:
            tasks.append((input, output, ext, options.sharpen))

    if options.workers > 1:
        producer = Producer(tasks)
        consumer = Consumer()

        with prodconsq.Mothership(producer, consumer, options.workers) as m:
            m.start()

if __name__ == '__main__':
    main()
