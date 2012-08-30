'''
Created on Jun 3, 2012

@author: ray
'''
import unittest
import os

from mason.core import Format
from mason.core.gridcrop import grid_crop, buffer_crop


class TestBufferCrop(unittest.TestCase):

    def testPNG(self):
        with open('./input/test_core_gridcrop_grid.png', 'r') as fp:
            data = fp.read()

        data = buffer_crop(data, 1024, 256, Format.PNG)

        with open('./output/buffer_crop.png', 'w') as fp:
            fp.write(data)

    def testJPG(self):
        with open('./input/test_core_gridcrop_grid.jpg', 'r') as fp:
            data = fp.read()

        data = buffer_crop(data, 1024, 256, Format.JPG)

        with open('./output/buffer_crop.jpg', 'w') as fp:
            fp.write(data)

    def testTIF(self):
        with open('./input/test_core_gridcrop_grid.tif', 'r') as fp:
            data = fp.read()

        data = buffer_crop(data, 1024, 256, Format.TIFF)

        with open('./output/buffer_crop.tif', 'w') as fp:
            fp.write(data)


class TestGridCrop(unittest.TestCase):

    def setUp(self):
        if not os.path.exists(r'./output/TestGridCrop'):
            os.mkdir(r'./output/TestGridCrop')

    def testPNG(self):
        with open('./input/test_core_gridcrop_grid.png', 'r') as fp:
            data = fp.read()

        datas = grid_crop(data, 4, 1024, 0, Format.PNG)
        self.assertEqual(len(datas), 16)

        for (x, y), d in datas.iteritems():
            with open(os.path.join(r'./output/TestGridCrop',
                                   '%d-%d.png' % (x, y)), 'wb') as fp:
                fp.write(d)

    def testJPG(self):
        with open('./input/test_core_gridcrop_grid.jpg', 'r') as fp:
            data = fp.read()

        datas = grid_crop(data, 4, 1024, 0, Format.JPG)
        self.assertEqual(len(datas), 16)

        for (x, y), d in datas.iteritems():
            with open(os.path.join(r'./output/TestGridCrop',
                                   '%d-%d.jpg' % (x, y)), 'wb') as fp:
                fp.write(d)


class TestGridCropBuffered(unittest.TestCase):

    def setUp(self):
        if not os.path.exists(r'./output/TestGridCropBuffered'):
            os.mkdir(r'./output/TestGridCropBuffered')

    def testPNG(self):
        with open('./input/test_core_gridcrop_grid.png', 'r') as fp:
            data = fp.read()

        size = (1024, 1024)
        crop_box = (256, 256, 768, 768)

        datas = grid_crop(data, 2, 512, 256, Format.PNG)
        self.assertEqual(len(datas), 4)

        for (x, y), d in datas.iteritems():
            with open(os.path.join(r'./output/TestGridCropBuffered',
                                   '%d-%d.png' % (x + 1, y + 1)), 'wb') as fp:
                fp.write(d)

    def testJPG(self):
        with open('./input/test_core_gridcrop_grid.jpg', 'r') as fp:
            data = fp.read()

        size = (1024, 1024)
        crop_box = (256, 256, 768, 768)

        datas = grid_crop(data, 2, 512, 256, Format.JPG)
        self.assertEqual(len(datas), 4)

        for (x, y), d in datas.iteritems():
            with open(os.path.join(r'./output/TestGridCropBuffered',
                                   '%d-%d.jpg' % (x + 1, y + 1)), 'wb') as fp:
                fp.write(d)


class TestMetatileFission(unittest.TestCase):
    pass

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
