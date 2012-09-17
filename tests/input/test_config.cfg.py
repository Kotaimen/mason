
source1 = dict(\
    name='roads',
    prototype='datasource.mapnik',
    cache=None,

    theme='./input/world.xml',
    image_type='png',
    )
    
source3 = dict(\
    name='roads',
    prototype='datasource.mapnik',
    cache=None,

    theme='./input/world.xml',
    image_type='png',
    )


source2 = dict(\
    name='srtm30',
    prototype='datasource.postgis',
    cache=None,

    server='172.26.183.198',
    table='srtm30',
    )

processor1 = dict(\
    name='hillshading_1',
    prototype='processor.hillshading',
    sources=source2,
    cache=None,

    zfactor=2,
    scale=111120,
    altitude=45,
    azimuth=315,
    )

processor2 = dict(\
    name='hillshading_2',
    prototype='processor.hillshading',
    sources=source2,
    cache=None,

    zfactor=2,
    scale=111120,
    altitude=55,
    azimuth=135,
)

composite = dict(\
     name='composite_1',
     prototype='composite.imagemagick',
     sources=(source1, source3),
     command='',
)


ROOT = dict(
            name='test',
            prototype='root',
            metadata=dict(tag='test'),
            pyramid=dict(),
            renderer=composite,
            )
