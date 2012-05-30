'''
Created on May 2, 2012

@author: ray
'''

import os
import unittest
from mason.cartographer import create_cartographer


TEST_SVR = 'postgresql+psycopg2://postgres:123456@localhost:5432/world_dem'
TEST_TBL = 'world'
TEST_ENVELOPE = (103.9995833, 27.9995833, 104.5004167, 28.5004167)


def save_to_file(tag, ext, data):
    file_name = './output/test_cartographer_%(tag)s.%(ext)s' % \
                {'tag': tag, 'ext': ext}
    if os.path.exists(file_name):
        os.remove(file_name)
    with open(file_name, 'wb') as fp:
        fp.write(data)


class CartographerHillShadeTest(unittest.TestCase):

    def test_HillShade_256x256(self):
        cartographer = create_cartographer('hillshade',
                                           server=TEST_SVR,
                                           dem_table=TEST_TBL,
                                           scale=111120,
                                           data_type='gtiff')

        size = (256, 256)
        envelope = TEST_ENVELOPE
        render_data = cartographer.doodle(envelope, size)

        data = render_data.data
        data_type = render_data.data_type
        save_to_file('hillshade_256x256', data_type.ext, data)

        cartographer.close()

    def test_HillShade_512x512(self):
        cartographer = create_cartographer('hillshade',
                                           server=TEST_SVR,
                                           dem_table=TEST_TBL,
                                           scale=111120,
                                           data_type='gtiff')

        size = (512, 512)
        envelope = TEST_ENVELOPE
        render_data = cartographer.doodle(envelope, size)

        data = render_data.data
        data_type = render_data.data_type
        save_to_file('hillshade_512x512', data_type.ext, data)

        cartographer.close()

#    def test_HillShade_PNG(self):
#        cartographer = create_cartographer('hillshade',
#                                           server=TEST_SVR,
#                                           dem_table=TEST_TBL,
#                                           data_type='png')
#
#        size = (256, 256)
#        envelope = TEST_ENVELOPE
#        render_data = cartographer.doodle(envelope, size)
#
#        data = render_data.data
#        data_type = render_data.data_type
#        save_to_file('hillshade_png', data_type.ext, data)
#
#        cartographer.close()

#    def test_HillShade_JPEG(self):
#        cartographer = create_cartographer('hillshade',
#                                           server=TEST_SVR,
#                                           dem_table=TEST_TBL,
#                                           data_type='jpeg',
#                                           data_parameters={'quality': 95})
#
#        size = (256, 256)
#        envelope = TEST_ENVELOPE
#        render_data = cartographer.doodle(envelope, size)
#
#        data = render_data.data
#        data_type = render_data.data_type
#        save_to_file('hillshade_jpeg95', data_type.ext, data)
#
#        cartographer.close()


class GDALColorReliefTest(unittest.TestCase):

    def setUp(self):
        self._color_context = './input/HypsometricColors(Light).txt'

    def test_ColorRelief_256x256(self):
        color_context = self._color_context
        cartographer = create_cartographer('colorrelief',
                                           color_context=color_context,
                                           server=TEST_SVR,
                                           dem_table='world',
                                           data_type='gtiff')

        size = (256, 256)
        envelope = TEST_ENVELOPE
        render_data = cartographer.doodle(envelope, size)

        data = render_data.data
        data_type = render_data.data_type
        save_to_file('colorrelief_256x256', data_type.ext, data)

        cartographer.close()

    def test_ColorRelief_512x512(self):
        color_context = self._color_context
        cartographer = create_cartographer('colorrelief',
                                           color_context=color_context,
                                           server=TEST_SVR,
                                           dem_table='world',
                                           data_type='gtiff')

        size = (512, 512)
        envelope = TEST_ENVELOPE
        render_data = cartographer.doodle(envelope, size)

        data = render_data.data
        data_type = render_data.data_type
        save_to_file('colorrelief_512x512', data_type.ext, data)

        cartographer.close()

    def test_ColorRelief_PNG(self):
        color_context = self._color_context
        cartographer = create_cartographer('colorrelief',
                                           color_context=color_context,
                                           server=TEST_SVR,
                                           dem_table='world',
                                           data_type='png')

        size = (256, 256)
        envelope = TEST_ENVELOPE
        render_data = cartographer.doodle(envelope, size)

        data = render_data.data
        data_type = render_data.data_type
        save_to_file('colorrelief_png', data_type.ext, data)

        cartographer.close()

    def test_ColorRelief_JPEG(self):
        color_context = self._color_context
        cartographer = create_cartographer('colorrelief',
                                           color_context=color_context,
                                           server=TEST_SVR,
                                           dem_table='world',
                                           data_type='jpeg',
                                           data_parameters={'quality': 95})

        size = (256, 256)
        envelope = TEST_ENVELOPE
        render_data = cartographer.doodle(envelope, size)

        data = render_data.data
        data_type = render_data.data_type
        save_to_file('colorrelief_jpeg', data_type.ext, data)

        cartographer.close()


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
