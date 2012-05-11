'''
Created on May 7, 2012

@author: ray
'''
import os
import shutil
from mason.utils import Timer
from mason.cartographer import MapnikRaster


def main():

    envelope = (-180, -85, 180, 85)
    size_list = [(256, 256), (512, 512), (1024, 1024), (2048, 2048)]

    mapnik_maker = MapnikRaster(theme_root='./input/',
                               theme_name='worldaltas',
                               image_type='png')

    output_dir = r'output/mapnik_bench'
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.mkdir(output_dir)

    for size in size_list:
        output = os.path.join(output_dir, 'worldaltas_%d_%d.png' % size)
        with Timer():
            data = mapnik_maker.doodle(envelope, size)
        with open(output, 'w') as fp:
            fp.write(data)


if __name__ == '__main__':
    main()
