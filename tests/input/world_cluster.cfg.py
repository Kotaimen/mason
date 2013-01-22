source1 = dict(\
    prototype='datasource.mapnik',
#    cache=dict(prototype='metacache',
#               root='/tmp/tile/source1',
#               compress=False,
#               data_format='png'
#               ),
    theme=r'./tests/input/world.xml',
    image_type='png',
    buffer_size=0,
    scale_factor=2,
    )

ROOT = dict(\
    renderer='source1',
    metadata=dict(tag='world'),
    pyramid=dict(levels=range(0, 9),
                 zoom=4,
                 center=(121.5, 31),
                 format='png',
                 buffer=32),
#    cache=dict(prototype='filesystem',
#               root='/tmp/tile/world',
#               compress=False),
    cache=dict(prototype='cluster',
               stride=8,
               servers=['localhost:11211'],
               root='/tmp/tile/world',
               compress=False
               )
    )

