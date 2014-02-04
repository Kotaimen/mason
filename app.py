#!/usr/bin/env python
# -*- encoding: utf8 -*-

#import sys
#sys.path.insert(0, '/path/to/mason')

from tileserver import build_app

class Options(object):
    layers = [ 'path/to/config'
	]
    mode = 'hybrid'
    debug = False
    reload = False
    age = 0
    viewer = True

options = Options()
application = build_app(options)

#application.debug = True
