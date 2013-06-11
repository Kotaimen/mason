#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""
Simple tile map server supporting render a configuration online or attaching
to a existing tilestorage.

In most cases, which dataset is small, just configure the renderer to write simple
filesystem cache and put the generated directory behind a standard static file
server.

Created on Sep 9, 2012
@author: Kotaimen
"""

import argparse
import os
import urllib

import multiprocessing

from flask import Flask, abort, jsonify, current_app, request
from flask import _app_ctx_stack as stack
from werkzeug.serving import run_simple
from multiprocessing import Process

from mason import Mason, __version__ as VERSION , __author__ as AUTHOR
from mason.tilestorage import attach_tilestorage
from mason.config import create_render_tree_from_config
from mason.utils import date_time_string

from mason.mason import InvalidLayer, TileNotFound
from mason.core.pyramid import TileOutOfRange

#===============================================================================
# Arg Parser
#===============================================================================


def add_storage_or_renderer(mason, config, option):
    """ Guess given config is a renderer or storage"""
    if not os.path.exists(config):
        raise RuntimeError("Layer configuration not found: '%s'" % config)
    if os.path.isdir(config):
        mason.add_storage_layer(attach_tilestorage('filesystem', root=config))
    elif os.path.isfile(config) and config.endswith('.mbtiles'):
        mason.add_storage_layer(attach_tilestorage('mbtiles', database=config))
    elif os.path.isfile(config) and config.endswith('.cfg.py'):
        mason.add_renderer_layer(create_render_tree_from_config(config, option=option))
    else:
        raise RuntimeError("Don't know how to create layer for '%s'" % config)


def parse_args(args=None):
    parser = argparse.ArgumentParser(\
        description='''Simple Tile Server v%s''' % VERSION,
        epilog='''Tile server which included a tile map viewer to display
        layers of map tiles.  Can attach to a rendered storage or render
        on-the-fly from renderer configuration.
        To start a production server, put this behind wsgi server, like gunicorn.
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
                        help='''Enable debug mode, this disables "--reload" and
                        requests will be processed in single thread (default
                        is multi-processed).''',)

    parser.add_argument('-r', '--reload',
                        dest='reload',
                        default=False,
                        action='store_true',
                        help='''Restart server automatically on code and
                        configuration file change.  You can enable this option
                        in non-debug mode which is useful for testing render
                        configurations.  For mapnik layers, this will also
                        cause xml theme file being reloaded on each render request.
                        (which is slow)
                        ''',)

    parser.add_argument('-w', '--workers',
                        dest='workers',
                        default=multiprocessing.cpu_count(),
                        type=int,
                        help='''Number of worker processes, default is equal
                        to core number (%(default)s).  Note this option is ignored under
                        debug mode because process model don't support debugging.''',)

    parser.add_argument('-a', '--age',
                        dest='age',
                        default=0,
                        type=int,
                        help='''Tile expiration age in seconds, which is set in
                        http response header ,default is 0''',)

    parser.add_argument('-m', '--mode',
                        dest='mode',
                        default='hybrid',
                        choices=['hybrid', 'readonly', 'overwrite', 'dryrun',
                                 'h', 'r', 'o', 'd', ],
                        help='''Specify rendering mode for "renderer" layers.
                        default is "%(default)s".
                        Note this option will not effect layers attatching to existing
                        stroage.
                        "hybrid": read from stroage cache when possible, otherwise
                        render tile and populates the cache.
                        "readonly": read from cache, never triggers render, returns 404
                        error if tile does not exist.
                        "overwrite": always render tile and update cache.
                        "dryrun": always render tile but do not touch cache.  Use this options
                        while testing new render configuration.
                        '''
                        )

    # Convert "mode" argument to the one understands by Mason
    mode2mode = dict(hybrid='hybrid',
                     h='hybrid',
                     readonly='readonly',
                     r='readonly',
                     overwrite='overwrite',
                     o='overwrite',
                     dryrun='dryrun',
                     d='dryrun')

    options = parser.parse_args(args)
    options.threaded = False  # option disabled
    options.mode = mode2mode[options.mode]

#    print options
    return options

#===============================================================================
# Application Object
#===============================================================================

INDEX_TEMPLATE = u'''<!DOCTYPE html>
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
</html>'''


def check_mason_config(layer_configs, mode):
    print 'Checking Mason Config'
    mason = Mason()
    # Add storages
    for layer_config in layer_configs:
        print 'Adding layer from "%s"' % layer_config
        layer_option = dict(mode=mode)
        add_storage_or_renderer(mason, layer_config, layer_option)


class MasonApp(object):

    def __init__(self, app, options):
        self._app = app
        self._options = options
        self._mason = None

        p = Process(target=check_mason_config,
                    args=(options.layers, options.mode))
        p.start()
        p.join()
        if p.exitcode:
            raise RuntimeError('Mason Configure Error!')


    @property
    def mason(self):
        if self._mason is None:
            print 'Init Mason Tile Service'
            mason = Mason()
            # Add storages
            for layer_config in self._options.layers:
                print 'Adding layer from "%s"' % layer_config
                layer_option = dict(mode=self._options.mode)
                add_storage_or_renderer(mason, layer_config, layer_option)
            self._mason = mason
        return self._mason


def build_app(options):
    app = Flask(__name__)
    mason_context = MasonApp(app, options)

    @app.route('/')
    def index():
        return INDEX_TEMPLATE % {'version': VERSION }

    @app.route('/tilesvr.js')
    def js():
        # Use first layer as base layer
        layers = mason_context.mason.get_layers()
        baselayer_metadata = mason_context.mason.get_metadata(layers[0])
        min_level = min(baselayer_metadata['levels'])
        max_level = max(baselayer_metadata['levels'])
        lon = baselayer_metadata['center'][0]
        lat = baselayer_metadata['center'][1]
        zoom = baselayer_metadata['zoom']

        script = u'''var po = org.polymaps;
var map = po.map();
map.container(document.getElementById("map").appendChild(po.svg("svg")))
   .center({lat:%(lat)f, lon:%(lon)f})
   .zoomRange([%(min_level)d, %(max_level)d])
   .zoom(%(zoom)d);
''' % dict(lat=lat, lon=lon, min_level=min_level, max_level=max_level, zoom=zoom)

        for layer in layers:
            metadata = mason_context.mason.get_metadata(layer)
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
            tile_data, mimetype, mtime = mason_context.mason.craft_tile(tag, z, x, y)
        except TileNotFound:
            abort(404)
        except InvalidLayer:
            abort(405)
        except TileOutOfRange:
            abort(405)

        age = options.age  # 3600 * 24 * 3
        headers = {
                   'Content-Type': mimetype,
                   'Last-Modified': date_time_string(mtime),
                    }
        if age > 0:
            headers['Cache-Control'] = 'max-age=%d, public' % age
            headers['Expires'] = date_time_string(mtime + age)

        return tile_data, 200, headers

    @app.route('/tile/<tag>')
    def tile_from_lonlat(tag):
        try:
            lon = request.args.get('lon')
            lat = request.args.get('lat')
            lon, lat = float(lon), float(lat)
        except TypeError:
            abort(400)

        try:
            tile_data, mimetype, mtime = mason_context.mason.craft_tile_from_lonlat(tag, lon, lat)
        except TileNotFound:
            abort(404)
        except InvalidLayer:
            abort(405)
        except TileOutOfRange:
            abort(405)

        age = options.age  # 3600 * 24 * 3
        headers = {
                   'Content-Type': mimetype,
                   'Last-Modified': date_time_string(mtime),
                    }
        if age > 0:
            headers['Cache-Control'] = 'max-age=%d, public' % age
            headers['Expires'] = date_time_string(mtime + age)

        return tile_data, 200, headers

    @app.route('/tile/*')
    def layers():
        layers = mason_context.mason.get_layers()
        return jsonify(layers=layers)

    @app.route('/tile/<tag>/metadata.<ext>')
    def metadata(tag, ext):
        try:
            metadata = mason_context.mason.get_metadata(tag)
        except InvalidLayer:
            abort(405)
        print ext
        if ext == 'json':
            return jsonify(**metadata)
        elif ext == 'jsonp':
            jsonp = \
            '''grid({"attribution":"","bounds":%(envelope)s,"center":[0,0,4],
            "geocoder":"",
            "id":"mason",
            "maxzoom":%(maxzoom)s,
            "minzoom":%(minzoom)s,
            "name":"%(tag)s",
            "private":true,
            "scheme":"xyz",
            "tilejson":
            "2.0.0",
            "tiles":["http://localhost:8080/tile/%(tag)s/{z}/{x}/{y}.%(ext)s"],
            "webpage":"http://tiles.mapbox.com/mapbox/map/mapbox-streets"});
            ''' % dict(envelope=list(metadata['envelope']),
                       maxzoom=max(metadata['levels']),
                       minzoom=min(metadata['levels']),
                       tag=metadata['tag'],
                       ext=metadata['format']['extension'][1:],
                       )
            return jsonp
        else:
            abort(404)

    return app


def main():
    options = parse_args()

    app = build_app(options)
    host, port = tuple(options.bind.split(':'))

    use_reloader = options.reload
    if options.debug:
        app.debug = True

    if use_reloader:
        config_files = list(fn for fn in options.layers if fn.endswith('.cfg.py'))
    else:
        config_files = []

    run_simple(host, int(port), app,
               use_reloader=use_reloader,
               use_debugger=options.debug,
               extra_files=config_files,
               threaded=options.threaded,
               processes=(1 if (options.debug or options.threaded) else options.workers),
               )


if __name__ == '__main__':
    main()
