'''
Created on May 2, 2012

@author: ray
'''

import shutil
import os
import unittest
from mason.cartographer import CartographerFactory

create_cartographer = CartographerFactory


def save_to_file(tag, ext, data):
    file_name = './output/test_mapnik_%(tag)s.%(ext)s' % \
                {'tag': tag, 'ext': ext}
    if os.path.exists(file_name):
        os.remove(file_name)
    with open(file_name, 'wb') as fp:
        fp.write(data)


class TestMapnikMaker(unittest.TestCase):

    def testPNG(self):
        cartographer = create_cartographer('mapnik',
                                           theme='./input/world.xml',
                                           image_type='png')

        size = (512, 512)
        envelope = (0, 0, 180, 85)
        stream = cartographer.render(envelope, size)
        with open('./output/test_cartographer_mapnik_png.png', 'wb') as fp:
            shutil.copyfileobj(stream, fp)
        cartographer.close()

    def testPNG256(self):
        cartographer = create_cartographer('mapnik',
                                           theme='./input/world.xml',
                                           image_type='png256')

        size = (512, 512)
        envelope = (0, 0, 180, 85)
        stream = cartographer.render(envelope, size)
        with open('./output/test_cartographer_mapnik_png256.png', 'wb') as fp:
            shutil.copyfileobj(stream, fp)
        cartographer.close()

    def testPNGPalette(self):
        cartographer = create_cartographer('mapnik',
                                           theme='./input/world.xml',
                                           image_type='png',
                                           palette='./input/example-palette.act')

        size = (512, 512)
        envelope = (0, 0, 180, 85)
        stream = cartographer.render(envelope, size)
        with open('./output/test_cartographer_mapnik_pngpalette.png', 'wb') as fp:
            shutil.copyfileobj(stream, fp)
        cartographer.close()


    def testJPEG(self):
        cartographer = create_cartographer('mapnik',
                                           theme='./input/world.xml',
                                           image_type='jpeg60')

        size = (512, 512)
        envelope = (0, 0, 180, 85)
        stream = cartographer.render(envelope, size)
        with open('./output/test_cartographer_mapnik_jpeg.jpg', 'wb') as fp:
            shutil.copyfileobj(stream, fp)
        cartographer.close()


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
