#!/usr/bin/env python

""" A Simple HTTP Tile Server

Created on May 14, 2012
@author: Kotaimen
"""

import os, os.path
import pprint
import argparse
import time

# Use cherrypy as http server framework, we don't need ORM here
import cherrypy

import mason
from mason.utils import Timer

VERSION = '0.8'
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))

WEEKDAY_NAME = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
MONTH_NAME = [None,
              'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def date_time_string(self, timestamp=None):
    """ Convert a filesystem timestamp to http response time, taken
    from BaseHTTPRequestHandler.date_time_string() """

    if timestamp is None:
        timestamp = time.time()
    year, month, day, hh, mm, ss, wd, y, z = time.gmtime(timestamp)
    s = "%s, %02d %3s %4d %02d:%02d:%02d GMT" % (
            WEEKDAY_NAME[wd],
            day, MONTH_NAME[month], year,
            hh, mm, ss)
    return s


def create_root_object(options):

    class TileService(object):

        def __init__(self):
            self.mason = mason.create_mason_from_config(options.config,
                                                        options.mode)

        def shutdown(self):
            self.mason.close()

        @cherrypy.expose
        @cherrypy.tools.gzip(mime_types=['application/json', 'text/plain', 'text/html'])
        def default(self, alias, z, x, y, **options):
            z = int(z)
            x = int(x)
            y, ext = tuple(y.split('.', 1))
            y = int(y)

            logger = cherrypy.request.app.log.access_log

            with Timer('Tile(%s/%d/%d/%d) craft in %%(time)s.' % (alias, z, x, y),
                       logger.info, newline=False):
                data, metadata = self.mason.craft_tile(alias, z, x, y)

            response = cherrypy.serving.response
            response.headers['Content-Type'] = metadata['mimetype']
            response.headers['Content-Length'] = len(data)
            response.headers['Last-Modified'] = date_time_string(metadata['mtime'])

            response.body = data
            return response.body

        @cherrypy.expose
        @cherrypy.tools.json_out()
        def layers(self, alias):
            if alias == '*':

                return self.mason.get_layers()
            else:
                return self.mason.get_layer_metadata(alias)


    class Root(object):

        @cherrypy.expose
        def index(self):
            raise cherrypy.HTTPRedirect('/static/polyviewer.html')

        # Anything starts with "tile" goes to tile
        tile = TileService()

        # Anything starts with "static" maps to static directory
        @cherrypy.tools.staticdir(root=os.path.join(SCRIPT_DIR, 'static'), dir='')
        def static(self):
            return

    return Root()

# ========================================================================================    
# Entry
# ========================================================================================    

def parse_args():
    parser = argparse.ArgumentParser(description='''A Simple HTTP Tile Server''',
                                     epilog=\
'''By default, server is running in readonly mode and won't render anything.
NOTE:  this script uses cherrypy's built-in threaded server, which is fine
for serving static tiles, but if online tile rendering is enabled, backend may
not be thread-safe and may cause GIL problem (eg: when you have 32 Cores). In this case,
run a process based server like gunicorn is strongly recommended.  (Start WSGI server
use supplied wsgi.py)
''',
                                     usage='%(prog)s [OPTIONS]',
                                     )

    parser.add_argument('-c', '--config',
                        dest='config',
                        default='tileserver.cfg.py',
                        help='''Specify location of the configuration file, default
                        is tileserver.cfg.py in current script directory''',
                        metavar='FILE',
                        )

    parser.add_argument('-b', '--bind',
                        dest='bind',
                        default='127.0.0.1:8080',
                        help='''Specify host:port server listens to, default to
                        127.0.0.1:8080
                        ''',
                        )

    parser.add_argument('-w', '--workers',
                        dest='workers',
                        default=10,
                        type=int,
                        help='Number of cherrypy worker threads, default is 10',
                        )

    parser.add_argument('--mode', '-m',
                        dest='mode',
                        choices=['readonly', 'readwrite'],
                        default='readonly',
                        help='''Operate mode, set to "readonly" (the default value)
                        for read tile only from storage; set to "readwrite" enables
                        online rendering.
                        ''',
                        )

    parser.add_argument('-q', '--quiet',
                        dest='quiet',
                        action='store_true',
                        default=False,
                        help='''Do not write http response info to screen, automatic
                        enabled when production mode is on.'''
                        )

    parser.add_argument('-p', '--production',
                        dest='production',
                        action='store_true',
                        default=False,
                        help='Enable production mode and disables auto-reloading.')

    parser.add_argument('--access-log',
                        dest='access_log',
                        default='access.log',
                        help='Specify filename of access log',
                        metavar='FILE',
                       )

    parser.add_argument('--error-log',
                        dest='error_log',
                        default='error.log',
                        help='Specify filename of error log',
                        metavar='FILE',
                        )

    options = parser.parse_args()

    if options.production:
        options.quiet = False

    return options


def main():

    options = parse_args()
#    pprint.pprint(options)

    host, port = tuple(options.bind.rsplit(':', 1))

    # Overwrite cherrypy options
    cherrypy.config.update({'server.socket_host': host,
                            'server.socket_port': int(port),
                            'server.thread_pool': options.workers,
                            'log.screen': not options.quiet,
                            'log.access_file': options.access_log,
                            'log.error_file': options.error_log
                            })
    if options.production:
        cherrypy.config.update({'environment': 'production'})

    # Add tile server configuration to auto reload list
    cherrypy.engine.autoreload.files.add(options.config)

    # Mount application
    root = create_root_object(options)
    try:
        cherrypy.tree.mount(root)
        # Start server
        cherrypy.engine.start()
        cherrypy.engine.block()
    finally:
        root.tile.shutdown()


if __name__ == '__main__':
    main()
