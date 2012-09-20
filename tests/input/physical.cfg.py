source1 = dict(\
    name='physical',
    prototype='datasource.postgis',
    cache=dict(prototype='metacache',
               root='/tmp/physical/dem',
               compress=False,
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
               ),
    sources=(hillshading,),
    )


ROOT = dict(\
    metadata=dict(tag='world'),
    pyramid=dict(levels=range(0, 9),
                 format='png',
                 buffer=32),
    cache=dict(prototype='filesystem',
               root='/tmp/physical/world',
               compress=False),
    renderer=to_png,
    )
