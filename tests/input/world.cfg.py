# Sample render configuration file
# Peek with ./tileserver.py ./tests/input/world.cfg.py
# Or render with ./tilerenderer.py ./tests/input/world.cfg.py --stride=8 

source1 = dict(\
    prototype='node.mapnik',
    cache=dict(prototype='metacache',
               root='/tmp/tile/source1',
               compress=False,
               data_format='png'
               ),
    theme=r'./tests/input/world.xml',
    image_type='png',
    buffer_size=0, # disable mapnik internal buffering
    scale_factor=1, # make line thicker
    )

source2 = dict(\
    prototype='node.mapnik',
    cache=dict(prototype='metacache',
               root='/tmp/tile/source2',
               compress=False,
               data_format='png'
               ),
    theme=r'./tests/input/world.xml',
    image_type='png',
    buffer_size=0, # disable mapnik internal buffering
    scale_factor=1, # make line thicker
    )

composite = dict(\
    prototype='node.imagemagick',
     cache=dict(prototype='metacache',
                root='/tmp/tile/composite',
                compress=False,
                ),
     sources=('source1', 'source2'),
     command='''
     ( {{source1}} -virtual-pixel edge -blur 0x12 -spread 3 +noise gaussian )
     {{source2}} -compose hardlight -composite''',
     format='png',
     )

ROOT = dict(\
    metadata=dict(tag='world',
                  dispname='Test World',
                  ),
    pyramid=dict(levels=range(0, 9),
                 zoom=4,
                 center=(121.5, 31),
                 format='png',
                 buffer=32),
    cache=dict(prototype='filesystem',
               root='/tmp/tile/world',
               compress=False),
    renderer='composite',
    )

