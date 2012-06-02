'''
Created on Jun 3, 2012

@author: ray
'''
import unittest
from mason.utils import boxcrop


class TestCrop(unittest.TestCase):

    def testPNGBoxCrop(self):
        with open('./input/grid.png', 'r') as fp:
            data = fp.read()

        size = (1024, 1024)
        crop_box = (256, 256, 768, 768)

        data = boxcrop(data, 'png', size, crop_box)

        with open('./output/box_crop_png.png', 'w') as fp:
            fp.write(data)

    def testPNG256BoxCrop(self):
        with open('./input/grid256.png', 'r') as fp:
            data = fp.read()

        size = (1024, 1024)
        crop_box = (256, 256, 768, 768)

        data = boxcrop(data, 'png', size, crop_box)

        with open('./output/box_crop_png256.png', 'w') as fp:
            fp.write(data)

    def testGTIFFBoxCrop(self):
        with open('./input/grid.tif', 'r') as fp:
            data = fp.read()

        size = (1024, 1024)
        crop_box = (256, 256, 768, 768)

        data = boxcrop(data, 'tif', size, crop_box)

        with open('./output/box_crop_tif.tif', 'w') as fp:
            fp.write(data)

    def testJPEGBoxCrop(self):
        with open('./input/grid.jpg', 'r') as fp:
            data = fp.read()

        size = (1024, 1024)
        crop_box = (256, 256, 768, 768)

        data = boxcrop(data, 'jpg', size, crop_box)

        with open('./output/box_crop_jpg.jpg', 'w') as fp:
            fp.write(data)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
