#!/usr/bin/env python

""" Generate upper level tiles by scaling down lower level tiles (aka uplifting)

This script requires ImageMagick and bypasses most TileStorage internals for
efficiency.

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
from mason.tilelib import tile_coordiante_to_dirname


#logger = multiprocessing.log_to_stderr(level=logging.INFO)


def walk_layer_hashed(root, level, ext):
    level_root = os.path.join(root, '%02d' % level)
    pattern = re.compile(r'(\d+)-(\d+)-(\d)+\.' + ext)
    n = 0
    for base, dirs, files in os.walk(level_root):
        for filename in files:
            match = pattern.match(filename)
            if not match:
                continue

            z, x, y = tuple(map(int, match.groups()))

            if (x % 2) != 0 or (y % 2) != 0:
                continue

            input_names = [os.path.join(base, '%d-%d-%d.' % (z, x, y) + ext),
                           os.path.join(base, '%d-%d-%d.' % (z, x + 1, y) + ext),
                           os.path.join(base, '%d-%d-%d.' % (z, x, y + 1) + ext),
                           os.path.join(base, '%d-%d-%d.' % (z, x + 1, y + 1) + ext)]

            os.path.join(base, filename)

            dirname = os.path.join(*tile_coordiante_to_dirname(z - 1,
                                                               x // 2,
                                                               y // 2))
            output_name = os.path.join(root,
                                       dirname,
                                       '%d-%d-%d.%s' % (z - 1, x // 2,
                                                        y // 2, ext))
            n += 1
            yield input_names, output_name
    else:
        print 'Found %d tiles to uplift' % (n * 4)


def walk_layer_simple(root, level, ext):
    level_root = os.path.join(root, '%d' % level)
    pattern = re.compile(r'\d+\.' + ext)
    n = 0
    for base, dirs, files in os.walk(level_root):

        for filename in files:
            # level_root/x/y.ext
            if not pattern.match(filename):
                continue

            head, tail = os.path.split(base)
            z = level
            x = int(tail)
            y = int(filename.rsplit('.')[0])

            if (x % 2) != 0 or (y % 2) != 0:
                continue

            input_names = [os.path.join(head, '%d' % x, '%d.%s' % (y, ext)),
                           os.path.join(head, '%d' % (x + 1), '%d.%s' % (y, ext)),
                           os.path.join(head, '%d' % x, '%d.%s' % (y + 1, ext)),
                           os.path.join(head, '%d' % (x + 1), '%d.%s' % (y + 1, ext)),
                           ]

            output_name = os.path.join(root,
                                       '%d' % (z - 1),
                                       '%d' % (x // 2),
                                       '%d.%s' % (y // 2, ext))
            n += 1
            yield input_names, output_name
    else:
        print 'Found %d tiles to uplift' % (n * 4)


def do_uplift(input_names, output_name, ext, sharpen):

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
        os.link(input_name, os.path.join(output_dir, link_name))

    args = ['montage',
            '-quiet', '-limit', 'thread', '2',
            '-mode', 'concatenate', '-tile', '2x2',
            ]

    args.extend(link_names)
    args.extend(['-resize', '50%',
                 '-unsharp', str(sharpen)])
    args.append(output_name)
#    print ' '.join(args)
    try:
        subprocess.check_call(args, cwd=output_dir)
    finally:
        for link_name in link_names:
            os.unlink(link_name)


def do_uplift_one(args):
    input_list, output, ext, sharpen = args
#    print 'Uplifting "%s"' % output
    with Timer('Uplifted "%s" in %%(time)s' % output):
        do_uplift(input_list, output, ext, sharpen)


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
                        help='''Root directory of the the cache''',
                        metavar='FILE',
                        )

    parser.add_argument('-e', '--ext',
                        dest='ext',
                        choices=['png', 'tif'],
                        help='''Filename extension of the cache ''',
                        )

    parser.add_argument('-s', '--simple',
                        dest='simple',
                        default=False,
                        action='store_true',
                        help='''Whether the directory tree is simple, default
                        is False ''',
                        )

    parser.add_argument('-v', '--level',
                        dest='level',
                        type=int,
                        help='''Base level to uplift ''',
                        )

    parser.add_argument('-o', '--overwrite',
                        dest='overwrite',
                        default=False,
                        action='store_true',
                        help='''Overwrite existing tiles''',
                        )

    parser.add_argument('--sharpen',
                        dest='sharpen',
                        default=0,
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

    return options


def main():
    options = parse_args()
#    storage = create_tilestorage(prototype='filesystem',
#                                 tag='dontcare',
#                                 root=options.root,
#                                 ext=options.ext,
#                                 simple=options.simple
#                                 )
    if options.simple:
        gen = walk_layer_simple(options.root, options.level, options.ext)
    else:
        gen = walk_layer_hashed(options.root, options.level, options.ext)

    def task_gen():
        for n, (input_list, output) in enumerate(gen):
            if os.path.exists(output) and not options.overwrite:
                continue
            yield input_list, output, options.ext, options.sharpen

    if options.workers == 1:
        map(do_uplift_one, task_gen())
    else:
        pool = multiprocessing.Pool(options.workers)
        try:
            for i in pool.imap(do_uplift_one, task_gen(), 256):
                pass
        except Exception:
            pool.terminate()
            pool.join()

if __name__ == '__main__':
    main()

