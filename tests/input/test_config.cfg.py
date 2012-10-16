

source1 = dict(\
    prototype='datasource.mapnik',
    cache=None,

    theme='./input/world.xml',
    image_type='png',
    )

source3 = dict(\
    prototype='datasource.mapnik',
    cache=None,

    theme='./input/world.xml',
    image_type='png',
    )


source2 = dict(\
    prototype='datasource.postgis',
    cache=None,

    server='172.26.183.198',
    table='srtm30',
    )

processor1 = dict(\
    prototype='processor.hillshading',
    sources='source2',
    cache=None,

    zfactor=2,
    scale=111120,
    altitude=45,
    azimuth=315,
    )

processor2 = dict(\
    prototype='processor.hillshading',
    sources='source2',
    cache=None,

    zfactor=2,
    scale=111120,
    altitude=55,
    azimuth=135,
)

composite = dict(\
     prototype='composite.imagemagick',
     sources=('source1', 'source3'),
     command='',
     format='png',
)


ROOT = dict(
            prototype='root',
            metadata=dict(tag='test'),
            pyramid=dict(envelope=(-180, -90, 180, 90)),
            renderer='composite',
            )
