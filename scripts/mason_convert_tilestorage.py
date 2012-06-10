'''
Created on Jun 2, 2012

@author: Kotaimen
'''

import re
import os, os.path

from mason.tilestorage import create_tilestorage
from mason.core import Pyramid
def main():

    root = r'/Users/Kotaimen/proj/python_dev/geodata/hillshade'
    pyramid = Pyramid()

    storage = create_tilestorage('filesystem', 'foo',
                                 root=r'/Users/Kotaimen/proj/python_dev/geodata/modern-antique_relief/old_hillshade',
                                 ext='png',
                                 simple=False
                                 )

    for base, dirs, files in os.walk(root):
        for filename in files:
            match = re.match(r'\w+-(\d+)-(\d+)-(\d+).png', filename)
            if not match:
                continue
            z, x, y = tuple(map(int, match.groups()))
#            print z, x, y
            with open(os.path.join(base, filename), 'rb') as fp:
                tile = pyramid.create_tile(z, x, y, fp.read(), {})
                storage.put(tile)


if __name__ == '__main__':
    main()
