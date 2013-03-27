#!/usr/bin/env python
# -*- encoding: utf8 -*-

import sys
sys.path.insert(0, '/path/to/mason')

from tileserver import build_app


class Options(object):
    layers = ['/path/to/layerconfig', ]
    mode = 'hybrid'
    debug = False

options = Options()
application = build_app(options)
# application.debug = True
