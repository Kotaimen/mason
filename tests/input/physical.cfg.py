world = '/mnt/geodata/srtm30_new/world_tiled.tif'
dem90m_wr = '/mnt/geodata/SRTM_30_org/world_org/'
dem10m_us = '/mnt/geodata/DEM-Tools-patch/source/ned10m/'
st_helens = '/mnt/geodata/hires-dem/st-helens/st-helens_3857.tif'


hillshading = dict(\
    prototype='node.homebrewhillshade',
    dataset_path=[
                  world,  # 0
                  world,
                  world,
                  world,
                  world,
                  world,  # 5
                  world,
                  [world, dem90m_wr, ],
                  [world, dem90m_wr, ],
                  [world, dem90m_wr, ],
                  [world, dem90m_wr, ],  # 10
                  [world, dem90m_wr, dem10m_us],
                  [world, dem90m_wr, dem10m_us],
                  [
                   world,
                   dem90m_wr,
                   dem10m_us,
                   st_helens
                   ],
                  ],
    zfactor=10,
    scale=1,
    azimuth=315,
    )

postprocessing = dict(\
    prototype='node.imagemagick',
    sources=['hillshading'],
    format='png',
    command='''
    {{hillshading}}
    -brightness-contrast -5%%x-5%% -gamma 0.9
    '''
    )

ROOT = dict(\
    metadata=dict(tag='world'),
    pyramid=dict(levels=range(0, 19),
                 format='png',
                 buffer=32,
                 zoom=9),
    renderer='postprocessing',
    )
