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

    root = r'/Users/Kotaimen/proj/maps/modern-antique/tile/composition'
    pyramid = Pyramid()
    os.remove(r'/Users/Kotaimen/proj/maps/modern-antique/modern-antique-compsition.mbtiles')
    storage = create_tilestorage('mbtiles', 'modern-antique',
                                 database='/Users/Kotaimen/proj/maps/modern-antique/modern-antique-compsition.mbtiles',
                                 ext='jpg',
                                 )

    for base, dirs, files in os.walk(root):
        for filename in files:
            match = re.match(r'(\d+)-(\d+)-(\d+).png', filename)
            if not match:
                continue

            fullname = os.path.join(base, filename)
            print fullname

            data = subprocess.check_output(['convert',
                                           fullname,
                                           '-quality', '68%',
                                           'jpg:-'])

            print os.stat(fullname).st_size // 1024, '=>', len(data) // 1024
            z, x, y = tuple(map(int, match.groups()))
            if z > 7:
                return
            tile = pyramid.create_tile(z, x, y, data, {})
            storage.put(tile)


if __name__ == '__main__':
    main()
