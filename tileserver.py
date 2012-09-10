#!/usr/bin/env python
# -*- encoding: utf8 -*-

"""
Tile map server attach to a rendered tile storage

Created on Sep 9, 2012
@author: Kotaimen
"""

import os
import argparse

from mason.tilestorage import FileSystemTileStorage
from mason.utils import date_time_string
from flask import Flask, abort

def parse_args():
    parser = argparse.ArgumentParser(description='Debug Tile Server',
                                     epilog=\
'''Attaching to a rendered tile storage and serve tile map ''',
                                     usage='%(prog)s [OPTIONS]',
                                     )

    parser.add_argument(dest='storage',
                        type=str,
                        metavar='STORAGE',
                        help='''Specify location of the tilestorage, if a directory
                        is given, a FileSystemTileStorage will be assumed''',)

    parser.add_argument('-b', '--bind',
                        dest='bind',
                        default='127.0.0.1:8080',
                        help='''Specify host:port server listens to, default to
                        127.0.0.1:8080
                        ''',)

    parser.add_argument('--access-log',
                        dest='access_log',
                        default='access.log',
                        help='Specify filename of access log',
                        metavar='FILE',)

    parser.add_argument('--error-log',
                        dest='error_log',
                        default='error.log',
                        help='Specify filename of error log',
                        metavar='FILE',)

    options = parser.parse_args()
#    print options
    return options


def attach_tilestorage(options):
    dirname = options.storage
    assert os.path.isdir(dirname)
    storage = FileSystemTileStorage.from_config(os.path.join(dirname, FileSystemTileStorage.CONFIG_FILENAME))
    return storage


def build_app(options, storage):
    app = Flask(__name__)

    @app.route('/')
    def index():
        return u'''<!DOCTYPE html>
<html>
  <head>
    <title>Mason Tile Server (0.9)</title>
    <meta name="viewport" content="initial-scale=1,maximum-scale=1"/>
    <script type="text/javascript" src="static/polymaps.js"></script>
    <style type="text/css">
    @import url("static/polmaps.js");
    </style>
  </head>
  <body id="map">
    <script type="text/javascript" src="tilesvr.js"></script>
  </body>
</html>'''


    ext = storage.pyramid.format.extension[1:]
    mimetype = storage.pyramid.format.mimetype
    min_level = min(storage.pyramid.levels)
    max_level = max(storage.pyramid.levels)
    lon = storage.pyramid.center.lon
    lat = storage.pyramid.center.lat
    zoom = storage.pyramid.zoom
    tag = storage.metadata.tag


    @app.route('/tilesvr.js')
    def js():
        data = u'''var po = org.polymaps;
var map = po.map();
map.container(document.getElementById("map").appendChild(po.svg("svg")))
   .center({lat:%(lat)f, lon:%(lon)f})
   .zoomRange([%(min_level)d, %(max_level)d])
   .zoom(%(zoom)d)
map.add(
    po.image()
    .url("../tile/%(tag)s/{Z}/{X}/{Y}.%(ext)s")
    );
map.add(po.interact())
   .add(po.drag())
   .add(po.dblclick())
   .add(po.wheel().smooth(false))
   .add(po.compass().pan("none"))
   .add(po.hash());
''' % dict(lat=lat, lon=lon, min_level=min_level, max_level=max_level,
           zoom=zoom, tag=tag, ext=ext)
        return data, 200, {'Content-Type': 'application/json'}

    @app.route('/tile/<tag>/<int:z>/<int:x>/<int:y>.<ext>')
    def tile(tag, z, x, y, ext):
        tile_index = storage.pyramid.create_tile_index(z, x, y)
        tile = storage.get(tile_index)
        if tile is None:
            abort(404)
        data = tile.data
        mtime = tile.mtime

        return data, 200, {'Content-Type': mimetype,
                           'Last-Modified': date_time_string(mtime)}
    return app

def main():
    options = parse_args()
    storage = attach_tilestorage(options)
    app = build_app(options, storage)
    addr, port = tuple(options.bind.split(':'))
    app.run(host=addr, port=int(port), debug=True)

if __name__ == '__main__':
    main()
