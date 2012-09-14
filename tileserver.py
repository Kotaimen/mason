#!/usr/bin/env python
# -*- encoding: utf8 -*-

"""
Tile map server attach to a rendered tile storage

Created on Sep 9, 2012
@author: Kotaimen
"""

import os
import urllib
import argparse

from mason import Mason
from mason.utils import date_time_string
from flask import Flask, abort


def parse_args(args=None):
    parser = argparse.ArgumentParser(description='Tile Server',
                                     epilog=\
'''Attaching to a rendered tile storage and serve tile map ''',
                                     usage='%(prog)s STORAGES|RENDERERS [OPTIONS]',
                                     )

    parser.add_argument('-s', '--storage',
                        dest='storages',
                        type=str,
                        action='append',
                        metavar='STORAGE',
                        help='''Specify location of a tile storage to attach to.
                        if a existing directory is given, a FileSystemTileStorage
                        will be assumed.  If a filename with .mbtiles extension
                        is given, a MBTilesTileStorage will be assumed.''',)

#    parser.add_argument('-r', '--renderer',
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
                        127.0.0.1:8080
                        ''',)

    options = parser.parse_args(args)

#    print options
    return options


def build_app(options):
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
    @import url("static/polymaps.css");
    </style>
  </head>
  <body id="map">
    <script type="text/javascript" src="tilesvr.js"></script>
  </body>
</html>'''


    # Create layer manager
    mason = Mason()

    # Add storages
    for storage_config in options.storages:
        mason.add_storage_layer(pathname=storage_config)
    # Use first layer as base layer
    baselayer_metadata = mason.get_metadata(mason.get_layers()[0])
    min_level = min(baselayer_metadata['levels'])
    max_level = max(baselayer_metadata['levels'])
    lon = baselayer_metadata['center'][0]
    lat = baselayer_metadata['center'][1]
    zoom = baselayer_metadata['zoom']


#    storage = mason._layers.values()[0]
#    print storage
#    print storage.metadata

#    ext = storage.metadata['format']['extension'][1:]
#    mimetype = storage.metadata['format']['mimetype']

#    print '=' * 10, storage.metadata['tag']
#    print tag

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
        tile_data, mimetype, mtime = mason.craft_tile(tag, z, x, y)
        headers = {'Content-Type': mimetype,
                   'Last-Modified': date_time_string(mtime)}
        return tile_data, 200, headers
    return app


def main():
    options = parse_args()
    app = build_app(options)
    addr, port = tuple(options.bind.split(':'))
    app.run(host=addr, port=int(port), debug=True)

if __name__ == '__main__':
    main()
