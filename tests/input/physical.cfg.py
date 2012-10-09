source1 = dict(\
    name='physical',
    prototype='datasource.postgis',
    cache=dict(prototype='metacache',
               root='/tmp/physical/dem',
               compress=False,
               data_format='gtiff',
               ),
    server='postgresql://postgres:123456@172.26.183.198:5432/srtm30_new',
    table='srtm30_new',
    )

hillshading = dict(\
    name='hillshading',
    prototype='processing.hillshading',
    cache=dict(prototype='metacache',
               root='/tmp/physical/hillshading',
               compress=False,
               data_format='gtiff'
               ),
    sources=(source1,),
    zfactor=1,
    scale=1,
    altitude=45,
    azimuth=315,
    )

to_png = dict(\
    name='convertpng',
    prototype='processing.rastertopng',
    cache=dict(prototype='metacache',
               root='/tmp/physical/hillshading_png',
               compress=False,
               data_format='png'
               ),
    sources=(hillshading,),
    )


ROOT = dict(\
    metadata=dict(tag='world'),
    pyramid=dict(levels=range(7, 9),
                 format='png',
                 buffer=32),
    cache=dict(prototype='filesystem',
               root='/tmp/physical/world',
               compress=False),
    renderer=to_png,
    )
