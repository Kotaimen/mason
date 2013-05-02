

dem90m_wr = '/mnt/geodata/SRTM_30_org/world_3857'
dem10m_us = '/mnt/geodata/DEM-Tools-patch/source/ned10m_3857/'


hillshading = dict(\
    prototype='node.homebrewhillshade',
    dataset_path=[
                  dem90m_wr,
                  dem90m_wr,
                  dem90m_wr,
                  dem90m_wr,
                  dem90m_wr,
                  dem90m_wr,
                  dem90m_wr,
                  [dem90m_wr, ],
                  [dem90m_wr, ],
                  [dem90m_wr, ],
                  [
                   dem90m_wr,
                   dem10m_us
                   ],
                  ],
    zfactor=1,
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
