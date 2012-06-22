'''
Created on Jun 2, 2012

@author: Kotaimen
'''

import re
import os, os.path

import subprocess

from mason.tilestorage import create_tilestorage
from mason.core import Pyramid


def main():

    root = r'/tmp/input'
    pyramid = Pyramid()
    storage = create_tilestorage('mbtiles',
                                 'Classic',
                                 database='/tmp/output.mbtiles',
                                 ext='jpg',
                                 metadata=dict(description='a foo that baz',
                                               minzoom='3',
                                               maxzoom='6',
                                               version='1',
                                               center='0,0,3',)
                                 )
#    storage = create_tilestorage('filesystem', 'Classic ',
#                                root='/tmp/export',
#                                ext='jpg',
#                                simple=True,
#                                )

    for base, dirs, files in os.walk(root):
        for filename in files:
            match = re.match(r'(\d+)-(\d+)-(\d+).png', filename)
            if not match:
                continue
            z, x, y = tuple(map(int, match.groups()))

            if z not in [3, 4, 5, 6]:
                continue

            if storage.has(pyramid.create_tile_index(z, x, y)):
                continue

            fullname = os.path.join(base, filename)
            print fullname,

            data = subprocess.check_output(['convert',
                                           fullname,
                                           '-quality', '95%',
                                           'jpg:-'])

            print '(%dk -> %dk)' % (os.stat(fullname).st_size // 1024,
                                    len(data) // 1024)

            tile = pyramid.create_tile(z, x, y, data, {})
            storage.put(tile)


if __name__ == '__main__':
    main()
