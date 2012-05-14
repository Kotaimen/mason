#!/usr/bin/env python

'''
Created on May 14, 2012

@author: Kotaimen
'''

import os, os.path
import pprint
import optparse

# Use cherrypy as http server framework, we don't need ORM here
import cherrypy

VERSION = '0.8'
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))


def create_root_object(options):

    class TileService(object):

        def __init__(self):
            self.mason = None

        def shutdown(self):
            pass

        @cherrypy.expose
        @cherrypy.tools.gzip(mime_types=['application/json', 'text/plain', 'text/html'])
        def default(self, alias, z, x, y, **options):
            return 'Tile(%s/%s/%s/%s)' % (alias, z, x, y)

    class Root(object):

        @cherrypy.expose
        def index(self):
            raise cherrypy.HTTPRedirect('/static/index.html')

        # Anything starts with "tile" goes to tile
        tile = TileService()

        # Anything starts with "static" maps to static directory
        @cherrypy.tools.staticdir(root=os.path.join(SCRIPT_DIR, 'static'), dir='')
        def static(self):
            return

    return Root()


def parse_args():
    parser = optparse.OptionParser(description='''A Simple HTTP Tile Server''',
                                   epilog=\
'''Note: this script uses cherrypy's built-in threaded server, which is fine
for serving static tiles, but if online rendering is enabled, backend may
not be thread-safe and may (and will eventually) cause GIL problem.
Running a process based server like gunicorn is strongly recommended.
(Start WSGI server using wsgi.py)
''',
                                   usage='%prog [OPTIONS]',
                                   version=VERSION)

    parser.add_option('-c', '--config',
                      dest='config',
                      default='tileserver.cfg',
                      help='''Specify location of the configuration file, default
                      is tileserver.cfg in current script directory''',
                      metavar='FILE',
                      )

    parser.add_option('-b', '--bind',
                      dest='bind',
                      default='localhost:8080',
                      help='''Specify host:port server listens to, default to
                      localhost:8080
                      ''',
                      )

    parser.add_option('-w', '--workers',
                      dest='workers',
                      default=10,
                      type='int',
                      help='Number of cherrypy worker threads, default is 10',
                      )

    parser.add_option('-m', '--mode',
                      dest='mode',
                      choices=['readonly', 'hybrid'],
                      default='readonly',
                      help='''Operate mode, set to "readonly" (the default value)
                      for read tile only from storage; set to "hybrid" enables online rendering.
                      ''',
                      )

    parser.add_option('-q', '--quiet',
                      dest='quiet',
                      action='store_true',
                      default=False,
                      help='Do not write response info to screen'
                      )

    parser.add_option('-p', '--production',
                      dest='production',
                      action='store_true',
                      default=False,
                      help='Set production mode and disables auto-reloading')

    parser.add_option('--access-log',
                      dest='access_log',
                      default='access.log',
                      help='Specify filename of access log',
                      metavar='FILE',
                      )

    parser.add_option('--error-log',
                      dest='error_log',
                      default='error.log',
                      help='Specify filename of error log',
                      metavar='FILE',
                      )

    (options, _args) = parser.parse_args()

    return options


def main():

    options = parse_args()
#    pprint.pprint(options)

    host, port = tuple(options.bind.split(':', 1))

    # Overwrite cherrypy options
    cherrypy.config.update({'server.socket_hos': host,
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
