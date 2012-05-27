# Mason Configuration File
#
# Configures default mason tile server, this is actually a python script defines
# a list of layer configurations.


# A list of tile layers
LAYERS = [

    # LAYER 1 ------------------------------------------------------------------

    {
    'tag': 'worldatlas',
    'ext': 'png',
    'mimetype': 'image/png',
    'levels':  range(0, 10),
    'tile_size': 256,
    'envelope': (-180, -85.06, 180, 85.06),
    'center': (0, 0),
    'crs': 'ESPG:4326',
    'proj': 'ESPG:3857',
    'mode': 'default',

    # Data Source -=-=-=-=-=-=-=-=-=

    'source':
#         None,

        {
        'prototype': 'mapnik',
        'theme_root': './samples/themes/',
        'theme_name': 'worldaltas',
        'image_type': 'png',
        },

#         {
#          'prototype': 'composer',
#          'command': '$1 $2 -compose overlay -composite',
#          'sources': [
#                    {
#                    'prototype': 'colorrelief',
#                    'server': TEST_SVR,
#                    'dem_table': TEST_TBL,
#                    'color_context': './samples/HypsometricColors(Dark).txt',
#                    'image_type': 'png',
#                    },
#                    {
#                    'prototype': 'hillshade',
#                    'server': TEST_SVR,
#                    'dem_table': TEST_TBL,
#                    'image_type': 'png',
#                    },
#
#                    ],
#          'storages': [
#                    {
#                    'prototype': 'filesystem',
#                    'tag': 'colorrelief',
#                    'root': '/tmp/worldaltas/colorrelief/',
#                    'ext': 'png',
#                    'simple': True,
#                    },
#
#                    {
#                    'prototype': 'filesystem',
#                    'tag': 'hillshade',
#                    'root': '/tmp/worldaltas/hillshade/',
#                    'ext': 'png',
#                    'simple': True,
#                    },
#                    ]
#         },

    # Data Storage -=-=-=-=-=-=-=-=-=

    'storage':
#         None,

        {
        'prototype': 'cascade',
        'storages':
            [
            {
             'prototype': 'memcache',
             'servers': ['localhost:11211'],
            },
            {
             'prototype': 'filesystem',
             'root': '/tmp/worldaltas/',
             'ext': 'png',
             'simple': True,
            },
            {
             'prototype': 'default',
             'filename': r'./samples/checkboard256.png',
             'ext': 'png',
            },
            ],
        },

#         {
#         'prototype': 'mbtiles',
#         'tag': 'worldaltas',
#         'database': '/tmp/worldaltas.mbtiles',
#         'ext': 'png',
#         },


    'metadata':
        {
        'Description': 'Sample Map',
        }
    },

    # LAYER 2 -------------------------------------------------------------------

]
