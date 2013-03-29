

source1 = dict(\
    prototype='node.mapnik',
    theme='./input/world.xml',
    image_type='png',

    cache=dict(prototype='metacache',
                root='./output/test-mason_renderer/hillshading'
                ),
    )

source3 = dict(\
    prototype='node.mapnik',
    theme='./input/world.xml',
    image_type='png',
    )

source2 = dict(\
    prototype='node.raster',
    cache=None,
    dataset_path='./input/hailey.tif'
    )

processor1 = dict(\
    prototype='node.hillshading',
    sources='source2',
    keep_cache=True,
    cache=dict(prototype='metacache',
                root='./output/test-mason_renderer/hillshading'
                ),

    zfactor=[10, ] * 10,
    scale=111120,
    altitude=45,
    azimuth=315,
    )

composite = dict(\
     prototype='node.imagemagick',
     sources=('source1', 'source3', 'processor1'),
     command="""{{%(source)s}}""",
     command_params=dict(source='source1'),
     format='png',
)


ROOT = dict(
            metadata=dict(tag='test-mason_renderer'),
            pyramid=dict(envelope=(-180, -85, 180, 85)),
            renderer='composite',
            storage=dict(prototype='filesystem',
                         root='./output/test-mason_renderer'
                        )
       )
