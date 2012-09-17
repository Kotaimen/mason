# Sample render configuration file
# Peek with ./tileserver.py ./tests/input/world.cfg.py
# Or render with ./tilerenderer.py ./tests/input/world.cfg.py --stride=8 

source1 = dict(\
    name='world1',
    prototype='datasource.mapnik',
    cache=dict(prototype='metacache',
               root='/tmp/test',
               compress=False,
               ),
    theme=r'./tests/input/world.xml',
    image_type='png',
    buffer_size=0, # disable mapnik internal buffering
    scale_factor=1, # make line thicker
    )

ROOT = dict(\
    name='world',
    prototype='root',
    metadata=dict(tag='world'),
    pyramid=dict(levels=range(0, 9),
                 format='png',
                 buffer=32),
    cache=dict(prototype='metacache',
               root='/tmp/crop',
               compress=False),
    renderer=source1,
    )

