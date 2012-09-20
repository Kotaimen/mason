'''
Created on Sep 19, 2012

@author: ray
'''
import unittest
from mason.cartographer import CartographerFactory


class TestPostGIS(unittest.TestCase):

    def setUp(self):
        self._postgis = CartographerFactory('postgis',
          server='postgresql://postgres:123456@172.26.183.198:5432/srtm30_new',
          table='srtm30_new'
          )

    def testRender(self):
        size = (256, 256)
        envelope = (131, 60, 134, 64)
        data_stream = self._postgis.render(envelope, size)
        data_format = self._postgis.output_format

        self.assertEqual(data_format, 'GTIFF')

        with open(r'./output/test_postgis.tif', 'wb') as fp:
            fp.write(data_stream.getvalue())


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
