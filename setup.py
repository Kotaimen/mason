#!/usr/bin/env python
'''
Created on Apr 29, 2012

@author: Kotaimen
'''

from distutils.core import setup

packages = ['mason',
            ]

data_files = []

scripts = []

setup(name='mason',
    version='0.9.0',
    author='Kotaimen, Ray',
    author_email='kotaimen.c@gmail.com, gliese.q@gmail.com',
    description='Another map tile library reinvented',
    packages=packages,
    data_files=data_files,
    scripts=scripts,
)


