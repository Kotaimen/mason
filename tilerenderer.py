#!/usr/bin/env python

"""
Parallel Tile Renderer Using MetaTile

Using process based producer-consumer model thus can be run efficiently
on very large node.  (Distributed rendering not included, yet, sorry.)

Created on May 17, 2012
@author: Kotaimen
"""

import argparse
import multiprocessing, multiprocessing.sharedctypes
import logging
import ctypes
import time

from mason import create_mason_from_config
from mason.core import Envelope
from mason.utils import Timer

CPU_COUNT = multiprocessing.cpu_count()
VERSION = '0.8'
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


def metatiles_from_envelope(pyramid, levels, envelope, stride):
    envlope = Envelope.from_tuple(envelope)
    proj = pyramid.projector

    for z in levels:
        # Calculate envelope in tile coordinate
        left, top = proj.coord2tile(envlope.lefttop, z)
        right, bottom = proj.coord2tile(envlope.rightbottom, z)

        # Snap top left to nearest MetaTile
        top -= top % stride
        left -= left % stride

        # At least generate one MetaTile
        if right == left:
            right += 1
        if top == bottom:
            bottom += 1

        for x in xrange(left, right, stride):
            for y in xrange(top, bottom, stride):
#                print z, x, y, stride
                yield z, x, y, stride


def spawner(queue, statics, layer, pyramid, levels, envelope, stride):
    for z, x, y, stride in metatiles_from_envelope(pyramid, levels, envelope,
                                                   stride):
#        print 'queue.put',layer, z, x, y, stride
        queue.put((z, x, y, stride))


#===============================================================================
# Consumer
#===============================================================================

def slave(queue, statistics, options):
    setup_logger(options.logfile)
    mason = create_mason_from_config(options.config, options.mode)
    layer = mason.get_layer(options.layer)
    while True:
        job = queue.get()

        if job is None:
            mason.close()
            return

        z, x, y, stride = job
        tag = 'MetaTile[%s/%d/%d/%d@%d]' % (options.layer, z, x, y, stride)
        logger.info('Rendering %s...', tag)
        with Timer('...%s rendered in %%(time)s' % tag, logger.info, False):
            try:
                rendered = layer.render_metatile(z, x, y, stride, logger)
                if rendered:
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

def boss(options, statistics):
    logger.info('===== Start Rendering =====')
    mason = create_mason_from_config(options.config, options.mode)
    layer = mason.get_layer(options.layer)
    pyramid = layer.pyramid
    queue = multiprocessing.JoinableQueue(maxsize=QUEUE_LIMIT)

    # Start all workers
    for w in range(options.workers):
        logging.info('Starting slave #%d' % w)
        worker = multiprocessing.Process(name='slave#%d' % w,
                                         target=slave,
                                         args=(queue, statistics, options)
                                         )

        worker.daemon = True
        worker.start()

    # Start producer
    producer = multiprocessing.Process(name='tilespawner',
                                       target=spawner,
                                       args=(queue, statistics, layer, pyramid,
                                             options.levels, options.envelope,
                                             options.stride))
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

    parser = argparse.ArgumentParser(description='''Parallel Tile Renderer''',
                                     usage='%(prog)s [OPTIONS]',
                                     epilog=\
''' Use --test to some test render, if everything is fine, pick a MetaTile
stride according to available memory.  You can monitor rendering progress by
starting a readonly tile server.  Try different configurations before start
a large render, and monitor to memory/disk usage.   Remember if you render the
globe down to level 20 contain zillions of tiles, literally!
'''
                                    )

    parser.add_argument('-c', '--config',
                        dest='config',
                        default='tileserver.cfg.py',
                        help='''Specify location of the layer config file, default
                        is tileserver.cfg.py in current script directory, config
                        format is same as tileserver.''',
                        metavar='FILE',
                       )

    parser.add_argument('-l', '--layer',
                        dest='layer',
                        default='',
                        help='''Alias of tile layer to render, must be present in the
                        config file, by default, the first layer found in the config
                        will be used.'''
                       )

    parser.add_argument('-e', '--envelope',
                        dest='envelope',
                        default='',
                        help='''Envelope to render specify in left,bottom,right,top
                        in layer CRS, by default, envelope in layer config will
                        be used.'''
                       )

    parser.add_argument('-v', '--levels',
                        dest='levels',
                        default='',
                        help='''Tile layers to render as a list: (eg:1,2,3), by default
                        levels in layer config will be used'''
                        )

    parser.add_argument('-s', '--metatile-stride',
                        dest='stride',
                        default=4,
                        type=int,
                        help='''Stride of MetaTile, which is minim render units, must be
                        power of 2.  Larger value takes more memory while rendering,
                        default value is 4.
                        '''
                        )

    parser.add_argument('-o', '--overwrite',
                       dest='overwrite',
                       default=False,
                       action='store_true',
                       help='''Overwrite existing tiles without check the storage.''',
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

    parser.add_argument('--load-wkt',
                       dest='wkt',
                       default='',
                       help='''Load a MultiPolygon WKT file as render range, try
                       cover given polygon using as less MetaTile as possible (optional,
                       not implemented yet, requires python-gdal)''',
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
    handler = logging.FileHandler(log_file, 'w')
    handler.setFormatter(formatter)
    handler.setLevel(logging.WARNING)
    logger.addHandler(handler)


def verify_config(options):
    setup_logger(options.logfile)
    logger.info('===== Testing Configuration =====')

    logger.info('Loading config: "%s"', options.config)
    logger.info('Saving log to: "%s"', options.logfile)

    mason = create_mason_from_config(options.config, 'overwrite')
    layers = mason.get_layers()

    logger.info('Config has %d layer(s): %r', len(layers), layers)
    if not options.layer:
        options.layer = layers[0]
    logger.info('Rendering layer: "%s"', options.layer)

    metadata = mason.get_layer_metadata(options.layer)

    if not options.levels:
        options.levels = metadata['levels']
    else:
        options.levels = list(map(int, options.levels.split(',')))
    assert all((l in metadata['levels']) for l in options.levels), \
        'Invalid render levels'
    logger.info('Rendering level: %r', options.levels)

    if not options.envelope:
        options.envelope = metadata['envelope']
    else:
        options.envelope = tuple(map(float, options.envelope.split(',')))
    logger.info('Rendering Tiles inside envelope: %s', options.envelope)

    logger.info('Rendering MetaTiles: stride=%d', options.stride)
    logger.info('Rendering using %d workers with %d cores', options.workers,
                CPU_COUNT)

    if options.overwrite:
        options.mode = 'overwrite'
    else:
        options.mode = 'readwrite'

    logger.info('Rendering mode is "%s"', options.mode)

    logger.info('===== Configuration is OK =====')

    logger.info('===== Test Rendering %d Tiles =====' % options.test)
    layer = mason.get_layer(options.layer)
    gen = metatiles_from_envelope(layer.pyramid,
                                  options.levels,
                                  options.envelope,
                                  options.stride,
                                  )
    for n, (z, x, y, stride) in enumerate(gen):
        if n >= options.test:
            break
        tag = 'MetaTile[%s/%d/%d/%d@%d]' % (options.layer, z, x, y, stride)
        logger.info('Rendering %s...', tag)
        with Timer('...%s rendered in %%(time)s' % tag, logger.info, False):
            layer.render_metatile(z, x, y, stride)
    logger.info('===== Done =====')

    return options


def main():
    print '=' * 70
    print 'Parallel Tile Renderer, please be very patient.'
    print 'Press CTRL+C to break render process.'
    print '=' * 70
    options = parse_args()
    options = verify_config(options)

    if options.test > 0:
        print 'Turn off testing to start rendering'
        return
    timer = Timer('Rendering finished in %(time)s')

    statistics = multiprocessing.sharedctypes.Value(Statics, 0, 0, 0)

    try:
        timer.tic()
        boss(options, statistics)
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

