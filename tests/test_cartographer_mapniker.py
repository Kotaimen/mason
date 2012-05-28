'''
Created on May 2, 2012

@author: ray
'''
import os
import unittest
from mason.cartographer import create_cartographer


def save_to_file(tag, ext, data):
    file_name = './output/test_mapnik_' + tag + ext
    if os.path.exists(file_name):
        os.remove(file_name)
    with open(file_name, 'wb') as fp:
        fp.write(data)


class TestMapnikMaker(unittest.TestCase):

    def testTrueColor(self):
        cartographer = create_cartographer('mapnik',
                                           theme_root='./input/',
                                           theme_name='worldaltas',
                                           data_type='png')

        size = (256, 256)
        envelope = (-180, -85, 180, 85)
        render_data = cartographer.doodle(envelope, size)

        data = render_data.data
        data_type = render_data.data_type
        save_to_file('worldaltas', data_type.ext, data)

        cartographer.close()

    def testIndexColor(self):
        cartographer = create_cartographer('mapnik',
                                           theme_root='./input/',
                                           theme_name='worldaltas',
                                           data_type='png256',
                                           data_parameters={'colors': 5})

        size = (256, 256)
        envelope = (-180, -85, 180, 85)
        render_data = cartographer.doodle(envelope, size)

        data = render_data.data
        data_type = render_data.data_type
        save_to_file('worldaltas_index_color', data_type.ext, data)

        cartographer.close()

    def testTransparency(self):
        cartographer = create_cartographer('mapnik',
                                           theme_root='./input/',
                                           theme_name='worldaltas',
                                           data_type='png256',
                                           data_parameters={'transparency': 0})

        size = (256, 256)
        envelope = (-180, -85, 180, 85)
        render_data = cartographer.doodle(envelope, size)

        data = render_data.data
        data_type = render_data.data_type
        save_to_file('worldaltas_transparency', data_type.ext, data)

        cartographer.close()

    def testPalette(self):
        cartographer = create_cartographer('mapnik',
                                            theme_root='./input/',
                                            theme_name='worldaltas',
                                            data_type='png256',
                                            data_parameters={
                                            'palette': './input/example-palette.act',
                                            'colors': 5,
                                            }
                                            )

        size = (256, 256)
        envelope = (-180, -85, 180, 85)
        render_data = cartographer.doodle(envelope, size)

        data = render_data.data
        data_type = render_data.data_type
        save_to_file('worldaltas_palette', data_type.ext, data)

        cartographer.close()

    def testJPEG(self):
        jpeg_quality = 50
        cartographer = create_cartographer('mapnik',
                                    theme_root='./input/',
                                    theme_name='worldaltas',
                                    data_type='jpeg',
                                    data_parameters={
                                                     'quality': jpeg_quality,
                                                    }
                                    )

        size = (256, 256)
        envelope = (-180, -85, 180, 85)
        render_data = cartographer.doodle(envelope, size)

        data = render_data.data
        data_type = render_data.data_type
        save_to_file('worldaltas_jpeg50', data_type.ext, data)

        cartographer.close()

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
