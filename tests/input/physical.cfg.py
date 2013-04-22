

hillshading = dict(\
    prototype='node.homebrewhillshade',
#    dataset_path='/mnt/geodata/DEM-Tools-patch/source/ned100m',
    dataset_path='/mnt/geodata/DEM-Tools-patch/source/ned10m/',
    zfactor=1,
    scale=1,
    altitude=45,
    azimuth=315,
    )


ROOT = dict(\
    metadata=dict(tag='world'),
    pyramid=dict(levels=range(0, 15),
                 format='png',
                 buffer=32,
                 zoom=9),
    renderer='hillshading',
    )
