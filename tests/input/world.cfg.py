# Sample render configuration file
# Peek with ./tileserver.py ./tests/input/world.cfg.py
# Or render with ./tilerenderer.py ./tests/input/world.cfg.py --stride=8 

source1 = dict(\
    name='world1',
    prototype='datasource.mapnik',
    cache=dict(prototype='metacache',
               root='/tmp/tile/source1',
               compress=False,
               ),
    theme=r'./tests/input/world.xml',
    image_type='png',
    buffer_size=0, # disable mapnik internal buffering
    scale_factor=1, # make line thicker
    )

source2 = dict(\
    name='world2',
    prototype='datasource.mapnik',
    cache=dict(prototype='metacache',
               root='/tmp/tile/source2',
               compress=False,
               ),
    theme=r'./tests/input/world.xml',
    image_type='png',
    buffer_size=0, # disable mapnik internal buffering
    scale_factor=1, # make line thicker
    )

composite = dict(\
     name='composite',
     prototype='composite.imagemagick',
     cache=dict(prototype='metacache',
                root='/tmp/tile/composite',
                compress=False,
                ),
     sources=(source1, source2),
     command=''' $1 $2 -blur 12 -compose hardlight -composite''',
     format='png',
     )

ROOT = dict(\
    metadata=dict(tag='world'),
    pyramid=dict(levels=range(0, 9),
                 format='png',
                 buffer=32),
    cache=dict(prototype='filesystem',
               root='/tmp/tile/world',
               compress=False),
    renderer=composite,
    )

