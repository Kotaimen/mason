'''
Created on May 28, 2012

@author: ray
'''
import unittest
import json
from mason.core.format import Format


class TestFormat(unittest.TestCase):

    def testKnownFormats(self):
        formats = Format.get_known_formats()

        self.assertIn('JPG', formats)
        self.assertIn('PNG', formats)
        self.assertIn('PNG256', formats)
        self.assertIn('TIFF', formats)
        self.assertIn('GTIFF', formats)

    def testPNGFormat(self):
        fmt = Format.PNG
        self.assertTrue(Format.is_known_format(fmt))
        self.assertTrue(Format.is_raster(fmt))
        self.assertFalse(Format.is_georeferenced(fmt))

    def testGTiffFormat(self):
        fmt = Format.GTIFF
        self.assertTrue(Format.is_known_format(fmt))
        self.assertTrue(Format.is_raster(fmt))
        self.assertTrue(Format.is_georeferenced(fmt))

    def testUnknownFormat(self):
        fmt1 = json.loads('''{
        "mimetype": "image/jpeg",
        "name": "JPG",
        "extenson": ".jpg",
        "type": "raster",
        "georeferenced": "no",
        "driver": "JPEG"
        } ''')
        fmt2 = json.loads('''{
        "mimetype": "image/jpeg",
        "name": "JPG",
        "extenson": ".jpeg",
        "type": "raster",
        "georeferenced": "no",
        "driver": "JPEG"
        } ''')
        self.assertTrue(Format.is_known_format(fmt1))
        self.assertFalse(Format.is_known_format(fmt2))

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
