#!/usr/bin/env python
'''
Created on Apr 29, 2012

@author: Kotaimen
'''

from distutils.core import setup

packages = ['mason',
            'mason.cartographer',
            'mason.composer',
            'mason.core',
            'mason.renderer',
            'mason.tilestorage',
            'mason.utils',
            ]

data_files = ['static/polymaps.css', 'static/polymaps.js']

scripts = ['tileserver.py', 'tilerenderer.py', 'transtorage.py']

setup(
    name='mason',
    version='0.9.2',
    author='Kotaimen, Ray',
    author_email='kotaimen.c@gmail.com, gliese.q@gmail.com',
    description='Another map tile library reinvented',
    packages=packages,
    data_files=data_files,
    scripts=scripts,
    requires=[],  # XXX: later...
)


