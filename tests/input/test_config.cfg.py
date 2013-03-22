

source1 = dict(\
    prototype='node.mapnik',
    theme='./input/world.xml',
    image_type='png',
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

    zfactor=lambda z, x, y: 20 - z,
    scale=111120,
    altitude=45,
    azimuth=315,
    )

composite = dict(\
     prototype='node.imagemagick',
     sources=('source1', 'source3', 'processor1'),
     command='$1',
     fmt='png',
)


ROOT = dict(
            prototype='root',
            metadata=dict(tag='test-mason_renderer'),
            pyramid=dict(envelope=(-180, -85, 180, 85)),
            renderer='composite',
            storage=dict(prototype='filesystem', 
                         root='./output/test-mason_renderer'
                        )
       )
