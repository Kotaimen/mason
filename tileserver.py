#!/usr/bin/env python
# -*- encoding: utf8 -*-

"""
Tile map server attach to a rendered tile storage

Created on Sep 9, 2012
@author: Kotaimen
"""

import argparse
import os
import urllib

import multiprocessing

from flask import Flask, abort
from werkzeug.serving import run_simple

from mason import Mason, __version__ as VERSION , __author__ as AUTHOR
from mason.tilestorage import attach_tilestorage
from mason.renderconfig import create_render_tree_from_config
from mason.utils import date_time_string

from mason.mason import InvalidLayer, TileNotFound
from mason.core.pyramid import TileOutOfRange


def add_storage_or_renderer(mason, config, mode):
    """ Guess given config is a renderer or storage"""
    if not os.path.exists(config):
        raise RuntimeError("Layer configuration not found: '%s'" % config)
    if os.path.isdir(config):
        mason.add_storage_layer(attach_tilestorage('filesystem', root=config))
    elif os.path.isfile(config) and config.endswith('.mbtiles'):
        mason.add_storage_layer(attach_tilestorage('mbtiles', database=config))
    elif os.path.isfile(config) and config.endswith('.cfg.py'):
        mason.add_renderer_layer(create_render_tree_from_config(config, mode=mode))
    else:
        raise RuntimeError("Don't know how to create layer for '%s'" % config)


def parse_args(args=None):
    parser = argparse.ArgumentParser(\
        description='''Simple Tile Server v%s''' % VERSION,
        epilog='''Tile server which included a tile map viewer to display
        layers of map tiles.  Can attach to a rendered storage or render on-the-fly from
        renderer configuration.
        ''',
        usage='%(prog)s LAYERS [OPTIONS]',)

    parser.add_argument('layers',
                        type=str,
                        nargs='+',
                        metavar='LAYERS',
                        help='''Specify location of a tile storage to attach to.
                        if a existing directory is given, a FileSystemTileStorage
                        will be assumed.  If a filename with .mbtiles extension
                        is given, a MBTilesTileStorage will be assumed.  If
                        a filename with .cfg.py extension is given, a Renderer
                        tree configuration will be assumed. ''',)

#    parser.add_argument('-c', '--config',
#                        dest='renderers',
#                        type=str,
#                        action='append',
#                        metavar='RENDERER',
#                        help='''Specify location of a renderer configuration
#                        file.''',)

    parser.add_argument('-b', '--bind',
                        dest='bind',
                        default='127.0.0.1:8080',
                        help='''Specify host:port server listens to, default to
                        %(default)s.
                        ''',)

    parser.add_argument('-d', '--debug',
                        dest='debug',
                        default=False,
                        action='store_true',
                        help='''Enable debug mode, this enables "--reload" and
                        requests will be processed in single thread (default
                        is multi-processed).''',)

    parser.add_argument('-r', '--reload',
                        dest='reload',
                        default=False,
                        action='store_true',
                        help='''Restart server automatically on code and
                        configuration file change.  You can enable this option
                        in non-debug mode which is useful for testing render
                        configurations.''',)

    parser.add_argument('-w', '--workers',
                        dest='workers',
                        default=multiprocessing.cpu_count(),
                        type=int,
                        help='''Number of worker processes, default is equal
                        to core number (%(default)s).''',)

    parser.add_argument('-m', '--mode',
                        dest='mode',
                        default='hybrid',
                        choices=['hybrid', 'readonly', 'overwrite', 'dryrun',
                                 'h', 'r', 'o', 'd', ],
                        help='''Specify rendering mode when a renderer
                        configuration is given, default is "%(default)s", note
                        "mode" will only work with tile renderer layer.
                        '''
                        )

    mode2mode = dict(hybrid='default',
                     h='default',
                     readonly='readonly',
                     r='readonly',
                     overwrite='overwrite',
                     o='overwrite',
                     dryrun='dryrun',
                     d='dryrun')

    options = parser.parse_args(args)

    options.mode = mode2mode[options.mode]

#    print options
    return options


def build_app(options):
    app = Flask(__name__)

    @app.route('/')
    def index():
        return u'''<!DOCTYPE html>
<html>
  <head>
    <title>Mason Tile Server (v%(version)s)</title>
    <meta name="viewport" content="initial-scale=1,maximum-scale=1"/>
    <script type="text/javascript" src="static/polymaps.js"></script>
    <style type="text/css">
    @import url("static/polymaps.css");
    </style>
  </head>
  <body id="map">
    <script type="text/javascript" src="tilesvr.js"></script>
  </body>
</html>''' % {'version': VERSION }

    # Create layer manager
    mason = Mason()

    # Add storages
    for layer_config in options.layers:
        add_storage_or_renderer(mason, layer_config, options.mode)
    # Use first layer as base layer
    baselayer_metadata = mason.get_metadata(mason.get_layers()[0])
    min_level = min(baselayer_metadata['levels'])
    max_level = max(baselayer_metadata['levels'])
    lon = baselayer_metadata['center'][0]
    lat = baselayer_metadata['center'][1]
    zoom = baselayer_metadata['zoom']

    @app.route('/tilesvr.js')
    def js():
        script = u'''var po = org.polymaps;
var map = po.map();
map.container(document.getElementById("map").appendChild(po.svg("svg")))
   .center({lat:%(lat)f, lon:%(lon)f})
   .zoomRange([%(min_level)d, %(max_level)d])
   .zoom(%(zoom)d);
''' % dict(lat=lat, lon=lon, min_level=min_level, max_level=max_level, zoom=zoom)

        for layer in mason.get_layers():
            print 'Addind layer "%s"' % layer
            metadata = mason.get_metadata(layer)
            ext = metadata['format']['extension'][1:]
            tag = urllib.quote(layer)
            script += u'''map.add(
    po.image()
    .url("../tile/%(tag)s/{Z}/{X}/{Y}.%(ext)s")
    );
        ''' % dict(tag=tag, ext=ext)
        else:
            script += u'''map.add(po.interact())
           .add(po.drag())
           .add(po.dblclick())
           .add(po.wheel().smooth(false))
           .add(po.compass().pan("none"))
           .add(po.hash());'''

        return script, 200, {'Content-Type': 'application/x-javascript'}

    @app.route('/tile/<tag>/<int:z>/<int:x>/<int:y>.<ext>')
    def tile(tag, z, x, y, ext):
        try:
            tile_data, mimetype, mtime = mason.craft_tile(tag, z, x, y)
        except TileNotFound:
            abort(404)
        except InvalidLayer:
            abort(405)
        except TileOutOfRange:
            abort(405)
        headers = {'Content-Type': mimetype,
                   'Last-Modified': date_time_string(mtime)}
        return tile_data, 200, headers

    return app


def main():
    options = parse_args()

    app = build_app(options)
    host, port = tuple(options.bind.split(':'))

    if options.debug:
        app.debug = True

    use_reloader = (options.reload or options.debug)
    if use_reloader:
        config_files = list(fn for fn in options.layers if fn.endswith('.cfg.py'))
    else:
        config_files = []

    run_simple(host, int(port), app,
               use_reloader=use_reloader,
               use_debugger=options.debug,
               extra_files=config_files,
               threaded=False,
               processes=(1 if options.debug else options.workers),
               )

if __name__ == '__main__':
    main()
