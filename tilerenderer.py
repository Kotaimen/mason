#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
Parallel Tile Renderer

Using process based producer-consumer model thus can be run efficiently
on very large node.  (Distributed rendering not included, yet, sorry.)


Created on May 17, 2012
@author: Kotaimen
"""

import argparse
import multiprocessing
import multiprocessing.sharedctypes
import logging
import os
import ctypes
import time
import re

from mason import (__version__ as VERSION,
                   __author__ as AUTHOR,
                   create_render_tree_from_config,)
from mason.utils import create_temp_filename

# from mason import create_mason_from_config
from mason.core import Envelope, PyramidWalker, TileListPyramidWalker
from mason.utils import Timer, human_size

CPU_COUNT = multiprocessing.cpu_count()
QUEUE_LIMIT = 1024

# Global logger object, init in main()
logger = None


class Statics(ctypes.Structure):

    _fields_ = [('rendered', ctypes.c_longlong),
                ('skipped', ctypes.c_longlong),
                ('failed', ctypes.c_longlong)]

#===============================================================================
# Producer
#===============================================================================


def envelope_spawner(queue, statistics, options):
    renderer, options = verify_config(options)
    walker = PyramidWalker(renderer.pyramid,
                           levels=options.levels,
                           stride=options.stride,
                           envelope=options.envelope)
    count = 0
    for index in walker.walk():
        if not options.overwrite and renderer.has_metatile(index):
            logger.info('Skipping %r...', index)
            continue
        count += 1
        queue.put((count, index.z, index.x, index.y, index.stride))


def tilelist_spawner(queue, statistics, options):
    renderer, options = verify_config(options)
    walker = TileListPyramidWalker(renderer.pyramid,
                                   options.csv,
                                   levels=options.levels,
                                   stride=options.stride,
                                   envelope=options.envelope)
    count = 0
    for index in walker.walk():
        if not options.overwrite and renderer.has_metatile(index):
            logger.info('Skipping %r...', index)
            continue
        count += 1
        queue.put((count, index.z, index.x, index.y, index.stride))


#===============================================================================
# Consumer
#===============================================================================

def render_worker(queue, statistics, options):
    renderer, options = verify_config(options)
    setup_logger(options.logfile)

    while True:
        task = queue.get()

        if task is None:
            renderer.close()
            return

        count, z, x, y, stride = task
        index = renderer.pyramid.create_metatile_index(z, x, y, stride)

        logger.info('Rendering #%d: %r...' % (count, index))
        with Timer('... #%d finished in %%(time)s' % count, logger.info, False):
            try:
                metatile = renderer.render_metatile(index)
                if metatile:
                    statistics.rendered += 1
                else:
                    statistics.skipped += 1
            except Exception as e:
                statistics.failed += 1
                logger.exception('Error while rendering #%d: %r' % (count, index))
            finally:
                queue.task_done()

#===============================================================================
# Monitor
#===============================================================================


def monitor(options, statistics):
    logger.info('===== Start Rendering =====')

    # Task queue
    queue = multiprocessing.JoinableQueue(maxsize=QUEUE_LIMIT)

    workers = list()

    # Start all workers
    for w in range(options.workers):
        logging.info('Creating worker #%d', w)
        worker = multiprocessing.Process(name='worker#%d' % w,
                                         target=render_worker,
                                         args=(queue, statistics, options))
        worker.daemon = True
        workers.append(worker)

    # Start producer
    if options.csv:
        spawner = tilelist_spawner
    else:
        spawner = envelope_spawner
    producer = multiprocessing.Process(name='spawner',
                                       target=spawner,
                                       args=(queue, statistics, options,),)
    producer.daemon = True
    producer.start()

    # Sleep a little so producer can popularize the queue
    time.sleep(1)

    # Start
    for worker in workers:
        # Start the workers one by one to avoid starving
        time.sleep(0.1)
        logging.info('Starting worker #%d', w)
        worker.start()

    # Join the queue
    try:
        producer.join()
        queue.join()
    except KeyboardInterrupt:
        logger.info('===== Rendering Canceled =====')
    else:
        logger.info('===== Rendering Complete =====')
    finally:
        return statistics

#===============================================================================
# Argument & Checking
#===============================================================================


def parse_args():

    parser = argparse.ArgumentParser(description='''Single Node Tile Renderer''',
                                     usage='%(prog)s RENDERER_CONFIG [OPTIONS]',
                                     epilog='''Render tiles concurrently on a
single node use multiprocessing. (Distributed render system is left for
readers as a home exercise).''')

    parser.add_argument('config',
                        default='renderer.cfg.py',
                        help='''Specify location of render config file, default
                        is tileserver.cfg.py in current script directory, config
                        format is same as tileserver.''',
                        metavar='FILE',
                       )

    parser.add_argument('-e', '--envelope',
                        dest='envelope',
                        default='',
                        help='''Render area specified in
                        left,bottom,right,top layer CRS, by default, envelope
                        in layer configuration will be used.'''
                       )

    parser.add_argument('-l', '--levels',
                        dest='levels',
                        default='',
                        help='''Tile layers to render (eg:1,2,3,5-10), by
                        default levels in renderer config will be used'''
                        )

    parser.add_argument('-s', '--metatile-stride',
                        dest='stride',
                        default=1,
                        type=int,
                        help='''Stride of MetaTile, must be power of 2.  MetaTile
                        slightly increases render speed at the expense higher of memory
                        usage, and reduces possible labeling artificats. Default
                        value is %(default)s.
                        '''
                        )

    parser.add_argument('-o', '--overwrite',
                       dest='overwrite',
                       default=False,
                       action='store_true',
                       help='''Overwrite Metatiles even if they already exists
                       in cache.''',
                       )

    parser.add_argument('-t', '--test',
                        dest='test',
                        default=0,
                        type=int,
                        help='''Test configuration by render given number of MetaTiles then exit,
                        implies "-o", default is 0, note this does not start workers.''',
                        )

    parser.add_argument('--profile',
                        dest='profile',
                        default=False,
                        action='store_true',
                        help='''Enable profiling (only works with --test)''',
                        )

    parser.add_argument('-w', '--workers',
                       dest='workers',
                       default=CPU_COUNT,
                       type=int,
                       help='''Number of renderer worker processes, default to number of
                       processor cores (%d, retrieved form subprocess module).
                       ''' % CPU_COUNT,
                       )

    parser.add_argument('--log-file',
                       dest='logfile',
                       default='render.log',
                       help='''Specify filename of the render log.''',
                       metavar='FILE',
                       )

    parser.add_argument('-c', '--csv',
                       dest='csv',
                       default='',
                       help='''Load a CSV tile list file and render tiles in it''',
                       metavar='FILE',
                       )

    options = parser.parse_args()

    return options


def setup_logger(log_file, level=logging.DEBUG):
    global logger
    if logger is not None:
        return
    logger = multiprocessing.log_to_stderr(level=level)
    formatter = logging.Formatter('[%(asctime)s - %(levelname)s/%(processName)s] %(message)s')
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)
    handler.setLevel(logging.WARNING)
    logger.addHandler(handler)


def verify_config(options):

    if options.overwrite:
        options.mode = 'overwrite'
    else:
        options.mode = 'hybrid'

    render_option = dict(mode=options.mode)
    renderer = create_render_tree_from_config(options.config, render_option)

    if not options.levels:
        options.levels = renderer.pyramid.levels
    else:
        levels = []
        for level in options.levels.split(','):
            if re.match(r'^\d+$', level):
                levels.append(int(level))
            elif re.match(r'^\d+-\d+$', level):
                start, end = tuple(map(int, level.split('-')))
                for l in range(start, end + 1):
                    levels.append(l)
            else:
                pass
        options.levels = sorted(set(levels))

    assert all((l in renderer.pyramid.levels) for l in options.levels), \
        'Invalid render levels'

    if not options.envelope:
        options.envelope = renderer.pyramid.envelope.make_tuple()
    else:
        options.envelope = tuple(map(float, options.envelope.split(',')))

    return renderer, options


def test_render(renderer, options):
    logger.info('Loading renderer configuration: "%s"', options.config)
    logger.info('Logging to: "%s"', os.path.abspath(options.logfile))
    logger.info('Rendering mode is "%s"', options.mode)
    logger.info('Rendering level: %r', options.levels)
    logger.info('Rendering envelope: %s', options.envelope)
    logger.info('Rendering tile list: %s', options.csv)
    logger.info('Rendering using meta tile stride=%d', options.stride)
    logger.info('Rendering using %d workers on %d cores', options.workers,
                CPU_COUNT)
    logger.info('Test render %d Tiles' % options.test)

    if not options.csv:
        walker = PyramidWalker(renderer.pyramid,
                               levels=options.levels,
                               stride=options.stride,
                               envelope=options.envelope)
    else:
        walker = TileListPyramidWalker(renderer.pyramid,
                                       options.csv,
                                       levels=options.levels,
                                       stride=options.stride,
                                       envelope=options.envelope)

    for n, index in enumerate(walker.walk()):
        if n >= options.test:
            break
        logger.info('Rendering %s...', index)
        with Timer('%s rendered in %%(time)s' % index, logger.info, False):
            metatile = renderer.render_metatile(index)

    logger.info('Test complete')


#===============================================================================
# Entry
#===============================================================================

def main():

    options = parse_args()

    print '=' * 70
    print 'Parallel Tile Renderer (v%s), please be very patient.' % VERSION
    print 'Press CTRL+C to break render process...'
    print '=' * 70

    setup_logger(options.logfile)

    if options.test > 0:
        print 'Test configuration, turn off test to start rendering.'
        renderer, options = verify_config(options)
        if options.profile:
            import cProfile as profile
            import pstats
            stats = create_temp_filename(suffix='.pstats')
            profile.runctx('test_render(renderer, options)', globals(), locals(), stats)
            p = pstats.Stats(stats)
            p.strip_dirs().sort_stats('time', 'calls').print_stats(0.25)
            p.print_callers(0.2)
            p.print_callees(0.05)
        else:
            test_render(renderer, options)
        return

    timer = Timer('Rendering finished in %(time)s')
    statistics = multiprocessing.sharedctypes.Value(Statics, 0, 0, 0)

    try:
        timer.tic()
        monitor(options, statistics)
    finally:
        timer.tac()
        print '=' * 70
        print timer.get_message()
        print 'Rendered %d MetaTiles, skipped %d, failed %d.' % \
            (statistics.rendered, statistics.skipped, statistics.failed)
        if statistics.rendered > 0:
            speed_per_tile = 1.0 * timer.get_time() / \
                 (statistics.rendered * options.stride * options.stride)
            print 'Average speed: %s/tile' % Timer.human_time(speed_per_tile)
        else:
            print 'Rendered noting.'

        if statistics.failed > 0:
            print 'Please check error log'
        print '=' * 70

if __name__ == '__main__':
    main()
