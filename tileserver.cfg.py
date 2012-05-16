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
    'source':
#         None,
        
        {
        'prototype': 'mapnik',
        'theme_root': './samples/themes/',
        'theme_name': 'worldaltas',
        'image_type': 'png',
        },
    'storage':
#         None,
        
        {
        'prototype': 'filesystem',
        'tag': 'worldaltas',
        'root': '/tmp/worldaltas/',
        'ext': 'png',
        'simple': True,
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
