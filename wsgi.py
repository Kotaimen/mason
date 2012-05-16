""" Application wrapper so tile server can run from any WSGI server

Start gunicorn server use (under current directory):

    gunicorn -w 2 -b 0.0.0.0:8080 -t 30 wsgi:application

Set worker number to core number +1 if when online rendering
"""

import os, os.path
import sys
import atexit


import cherrypy

cherrypy.config.update({'enviroment': 'embedded'})

if cherrypy.engine.state == 0:
    cherrypy.engine.start(blocking=False)
    atexit.register(cherrypy.engine.stop)

#root = os.path.abspath(os.path.basename(os.path.dirname(__file__)))

import tileserver


class Options(object):
    """ Dummy option class """
    # Absolute path to configuration file
    config = os.path.abspath('tileserver.cfg.py')
    # Server mode, can be 'default' or 'readonly'
    mode = 'default'

application = cherrypy.Application(tileserver.create_root_object(Options()),
                                   script_name=None,
                                   config=None)
