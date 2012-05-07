'''
Created on May 7, 2012

@author: Kotaimen
'''

import os.path
import shutil

from mason.utils import Timer
from mason.cartographer.gdalutil import gdal_hillshade


def main():
    # See how fast gdal is

    input = r'./input/hailey.dem'
    output_dir = r'output/shaded_relief_bench'
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.mkdir(output_dir)

    for z in xrange(1, 4):
        for a in range(0, 360, 45):
            for l in range(15, 91, 15):
                output = os.path.join(output_dir, 'z=%s,a=%s,l=%s.tiff' % (z, a, l))
                with Timer():
                    gdal_hillshade(input,
                                   output,
                                   zfactor=z,
                                   scale=111120,
                                   azimuth=a,
                                   altitude=l,)


if __name__ == '__main__':
    main()
