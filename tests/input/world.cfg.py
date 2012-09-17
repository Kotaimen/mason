
source1 = dict(\
    name='world1',
    prototype='datasource.mapnik',
    cache=None,
    theme=r'./tests/input/world.xml',
    image_type='png',
    buffer_size=0,
    scale_factor=4,
    )
    
    
ROOT = dict(\
    name='world',
    prototype='root',
    format='png',
    metadata=dict(tag='world'),
    pyramid=dict(levels=range(0,9),buffer=0),
    renderer=source1,
    
    )
