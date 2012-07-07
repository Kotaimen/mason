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
            'mason.tilelayer',
            'mason.tilesource',
            'mason.tilestorage',
            'mason.utils']

data_files = []

scripts = ['tileserver.py', 'tilerenderer.py']

setup(name='mason',
    version='0.8.0',
    author='Kotaimen, Ray',
    author_email='kotaimen.c@gmail.com, gliese.q@gmail.com',
    description='Another map tile library reinvented',
    packages=packages,
    data_files=data_files,
    scripts=scripts,
)


