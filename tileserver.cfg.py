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
        {
         'prototype': 'composer',
         'command': '''
         # Background
         $1
         # Land outer shadow
         (
             $2 -channel A
             -blur 0x12 -spread 2
             -evaluate Multiply 0.5
             +channel
             -fill black -colorize 100%
         ) -compose Multiply -composite
         # Landmass
         $2 -compose over -composite
         # Borders
         (
            $3 -channel A
            -morphology erode disk:2
            +channel
         ) -compose over -composite
         -fill blue -tint 96
         ''',
         'buffer_size': 32,
         'tilelayers': [
                        {
                         'prototype': 'cartographer',
                         'source': {
                                    'prototype': 'mapnik',
                                    'theme_root': './samples/themes',
                                    'theme_name': 'worldaltas_sea',
                                    'data_type': 'png',
                                    }
                         },
                        {
                         'prototype': 'cartographer',
                         'source': {
                                    'prototype': 'mapnik',
                                    'theme_root': './samples/themes/',
                                    'theme_name': 'worldaltas_land',
                                    'data_type': 'png',
                                    }
                         },
                        {
                         'prototype': 'cartographer',
                         'source': {
                                    'prototype': 'mapnik',
                                    'theme_root': './samples/themes/',
                                    'theme_name': 'worldaltas_line',
                                    'data_type': 'png',
                                    }
                         },
                        ]
         },

    # Data Storage -=-=-=-=-=-=-=-=-=

    'storage':
         None,
#
#        {
#        'prototype': 'cascade',
#        'storages':
#            [
#            {
#             'prototype': 'memcache',
#             'servers': ['localhost:11211'],
#            },
#            {
#             'prototype': 'filesystem',
#             'root': '/tmp/worldaltas/',
#             'ext': 'png',
#             'simple': True,
#            },
#            {
#             'prototype': 'default',
#             'filename': r'./samples/checkboard256.png',
#             'ext': 'png',
#            },
#            ],
#        },
    'metadata':
        {
        'Description': 'Sample Map',
        }
    },

    # LAYER 2 -------------------------------------------------------------------

]
