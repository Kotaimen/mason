#!/usr/bin/env python
# -*- encoding: utf8 -*-

import sys
#sys.path.insert(0, '/path/to/the/application')

from tileserver import build_app


class Options(object):
    layers = ['/path/to/layer', ]

options = Options()
application = build_app(options)

