#!/usr/bin/env python

"""
Parallel Tile Renderer

Using process based producer-consumer model thus can be run efficiently
on very large node.  (Distributed rendering not included, yet, sorry.)

Created on May 17, 2012
@author: Kotaimen
"""

import argparse
import multiprocessing, multiprocessing.sharedctypes
import logging
import os
import ctypes
import time

from mason import (__version__ as VERSION,
                   __author__ as AUTHOR,
                   create_render_tree_from_config)

#from mason import create_mason_from_config
from mason.core import Envelope, PyramidWalker
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


def spawner(queue, statistics, options):
    renderer = create_render_tree_from_config(options.config, 'readonly')
    walker = PyramidWalker(renderer.pyramid,
                           levels=options.levels,
                           stride=options.stride,
                           envelope=options.envelope)
    for index in walker.walk():
#        print index
        queue.put((index.z, index.x, index.y, index.stride))


#===============================================================================
# Consumer
#===============================================================================

def worker(queue, statistics, options):
    setup_logger(options.logfile)
    renderer = create_render_tree_from_config(options.config, options.mode)

    while True:
        task = queue.get()

        if task is None:
            renderer.close()
            return

        z, x, y, stride = task
        index = renderer.pyramid.create_metatile_index(z, x, y, stride)

        logger.info('Rendering %r...', index)
        with Timer('...%r rendered in %%(time)s' % index, logger.info, False):
            try:
                metatile = renderer.render(index)
                if metatile:
                    statistics.rendered += 1
                else:
                    statistics.skipped += 1
            except Exception as e:
                statistics.failed += 1
                logger.exception(e)
            finally:
                queue.task_done()

#===============================================================================
# Monitor
#===============================================================================


def monitor(options, statistics):
    logger.info('===== Start Rendering =====')

    # Task queue
    queue = multiprocessing.JoinableQueue(maxsize=QUEUE_LIMIT)

    # Start all workers
    for w in range(options.workers):
        logging.info('Starting worker #%d' % w)
        process = multiprocessing.Process(name='worker#%d' % w,
                                          target=worker,
                                          args=(queue, statistics, options))
        process.daemon = True
        process.start()

    # Start producer
    producer = multiprocessing.Process(name='spawner',
                                       target=spawner,
                                       args=(queue, statistics, options,),)
    producer.daemon = True
    producer.start()

    # Sleep a little so producer can popularize the queue
    time.sleep(1)

    # Join the queue
    try:
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
                                     epilog=\
'''Render tiles concurrently on a single node use process based
producer->queue->consumer model. Note: if you render the entire globe
down to level 20, there will be zillions of tiles, literally!
(Distributed render system is left for readers as a home exercise ).
'''
                                    )

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
                        help='''Envelope to render specify in
                        left,bottom,right,top in layer CRS, by default, envelope
                        in layer configuration will be used.'''
                       )

    parser.add_argument('-l', '--levels',
                        dest='levels',
                        default='',
                        help='''Tile layers to render as a list: (eg:1,2,3), by
                        default levels in renderer config will be used'''
                        )

    parser.add_argument('-s', '--metatile-stride',
                        dest='stride',
                        default=1,
                        type=int,
                        help='''Stride of MetaTile, must be power of 2.  MetaTile
                        increases render speed at the expense higher of memory
                        usage. Default value is %(default)s.
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
                        help='''Test configuration by just given number of MetaTiles,
                        implies "-o", default is 0, note this does not start workers.''',
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

#    parser.add_argument('--load-wkt',
#                       dest='wkt',
#                       default='',
#                       help='''Load a MultiPolygon WKT file as render range, try
#                       cover given polygon using as less MetaTile as possible (optional,
#                       not implemented yet, requires python-gdal)''',
#                       metavar='FILE',
#                       )

    options = parser.parse_args()

    return options


def setup_logger(log_file, level=logging.DEBUG):
    global logger
    if logger is not None:
        return
    logger = multiprocessing.log_to_stderr(level=level)
    formatter = logging.Formatter('[%(asctime)s - %(levelname)s/%(processName)s] %(message)s')
    handler = logging.FileHandler(log_file, 'w')
    handler.setFormatter(formatter)
    handler.setLevel(logging.WARNING)
    logger.addHandler(handler)


def verify_config(options):
    setup_logger(options.logfile)

    logger.info('===== Testing Configuration =====')

    logger.info('Loading renderer configuration: "%s"', options.config)
    logger.info('Saving log to: "%s"', os.path.abspath(options.logfile))

    if options.overwrite:
        options.mode = 'overwrite'
    else:
        options.mode = 'default'
    logger.info('Rendering mode is "%s"', options.mode)

    renderer = create_render_tree_from_config(options.config,
                                              {'mode': options.mode})

    if not options.levels:
        options.levels = renderer.pyramid.levels
    else:
        options.levels = list(map(int, options.levels.split(',')))
    assert all((l in renderer.pyramid.levels) for l in options.levels), \
        'Invalid render levels'
    logger.info('Rendering level: %r', options.levels)

    if not options.envelope:
        options.envelope = renderer.pyramid.envelope.make_tuple()
    else:
        options.envelope = tuple(map(float, options.envelope.split(',')))
    logger.info('Rendering envelope: %s', options.envelope)

    logger.info('Rendering using meta tile stride=%d', options.stride)
    logger.info('Rendering using %d workers on %d cores', options.workers,
                CPU_COUNT)

    logger.info('===== Configuration is OK =====')

    logger.info('===== Test Rendering %d Tiles =====' % options.test)

    walker = PyramidWalker(renderer.pyramid,
                           levels=options.levels,
                           stride=options.stride,
                           envelope=options.envelope)

    for n, index in enumerate(walker.walk()):
        if n >= options.test:
            break
        logger.info('Rendering %s...', index)
        with Timer('%s rendered in %%(time)s' % index, logger.info, False):
            metatile = renderer.render(index)

    renderer.close()

    logger.info('===== Done =====')

    return options


def main():
    options = parse_args()

    print '=' * 70
    print 'Parallel Tile Renderer (v%s), please be very patient.' % VERSION
    print 'Press CTRL+C to break render process...'
    print '=' * 70
    options = verify_config(options)

    if options.test > 0:
        print 'Turn off testing to start rendering'
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

