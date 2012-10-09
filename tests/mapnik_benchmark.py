'''
Created on May 7, 2012

@author: kotaimen
'''
import os
import threading
import shutil
from mason.utils import Timer
from mason.cartographer import create_cartographer


def benchmark():

    envelope = (-180, -85, 180, 85)
    size_list = [(256, 256), (512, 512), (1024, 1024), (2048, 2048)]

    mapniker = create_cartographer('mapnik',
                                   theme='./input/world.xml',
                                   image_type='jpeg')
    output_dir = r'output/mapnik_benchmark'
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.mkdir(output_dir)

    for size in size_list:
        output = os.path.join(output_dir, 'world_%dx%d.jpg' % size)
        with Timer():
            data = mapniker.render(envelope, size)
            with open(output, 'wb') as fp:
                shutil.copyfileobj(data, fp)
                data.close()


def render(n, mapniker):
    for i in range(55):
        print 'thread %d #%d' % (n, i)
        data = mapniker.render((-180, -85, 180, 85), (100 + i, 100 + i))
        output = os.path.join(r'output/mapnik_benchmark', 'mt_%d_%03d.png' % (n, i))
        with open(output, 'wb') as fp:
            shutil.copyfileobj(data, fp)
        data.close()


def multithread_render():
    mapniker = create_cartographer('mapnik',
                                   theme='./input/world.xml',
                                   image_type='png')
    threads = list()
    for i in range(4):
        thread = threading.Thread(target=render, args=(i, mapniker,))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()

if __name__ == '__main__':
    benchmark()
    multithread_render()
