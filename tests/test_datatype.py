'''
Created on May 28, 2012

@author: ray
'''
import unittest

from mason.core.datatype import create_data_type


class DataTypeTest(unittest.TestCase):

    def testPNGDataType(self):
        data_type = create_data_type('png')
        self.assertEqual(data_type.name, 'png')
        self.assertEqual(data_type.ext, 'png')
        self.assertEqual(data_type.mimetype, 'image/png')
        self.assertEqual(data_type.parameters, None)

    def testPNG256DataType(self):
        data_type = create_data_type('png256')
        self.assertEqual(data_type.name, 'png256')
        self.assertEqual(data_type.ext, 'png')
        self.assertEqual(data_type.mimetype, 'image/png')
        self.assertEqual(data_type.parameters, None)

        params = dict(colors=256, transparency=1)
        data_type = create_data_type('png256', params)
        self.assertEqual(data_type.name, 'png256')
        self.assertEqual(data_type.ext, 'png')
        self.assertEqual(data_type.mimetype, 'image/png')
        self.assertEqual(data_type.parameters['colors'], 256)
        self.assertEqual(data_type.parameters['transparency'], 1)

    def testGTiffDataType(self):
        data_type = create_data_type('gtiff')
        self.assertEqual(data_type.name, 'gtiff')
        self.assertEqual(data_type.ext, 'tif')
        self.assertEqual(data_type.mimetype, 'image/tiff')
        self.assertEqual(data_type.parameters, None)

    def testJPEGDataType(self):
        data_type = create_data_type('jpeg')
        self.assertEqual(data_type.name, 'jpeg')
        self.assertEqual(data_type.ext, 'jpg')
        self.assertEqual(data_type.mimetype, 'image/jpeg')
        self.assertEqual(data_type.parameters, None)

        params = dict(quality=80)
        data_type = create_data_type('jpeg', params)
        self.assertEqual(data_type.name, 'jpeg')
        self.assertEqual(data_type.ext, 'jpg')
        self.assertEqual(data_type.mimetype, 'image/jpeg')
        self.assertEqual(data_type.parameters['quality'], 80)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
