'''
Created on May 2, 2012

@author: ray
'''
import sqlalchemy
from sqlalchemy.orm import scoped_session, sessionmaker

from ..utils.gdalutil import gdal_warp
from ..core import RenderData
from .cartographer import Cartographer


DEM_DATA_QUERY = '''
SELECT
ST_ASGDALRASTER(
ST_UNION(ST_CLIP(the_rast, %(bbox)s, true)), 
'GTIFF', ARRAY['PIXELTYPE=SIGNEDBYTE','PROFILE=GeoTIFF'])
AS dem_data
FROM %(table)s
WHERE ST_INTERSECTS(the_rast, %(bbox)s)
'''

def _buffer_envelope(envelope, size, buffer_size):
    width, height = size
    minx, miny, maxx, maxy = envelope
    
    diff_x = abs(maxx - minx)
    diff_y = abs(maxy - miny)
    
    buffer_x = diff_x / width * buffer_size
    buffer_y = diff_y / height * buffer_size
    
    new_envelope = (minx - buffer_x,
                    miny - buffer_y,
                    maxx + buffer_x,
                    maxy + buffer_y)
    
    return new_envelope
    

#==============================================================================
# Base class of GDAL DEM Raster Maker
#==============================================================================
class DEMRaster(Cartographer):

    """ Render a raster map from PostGIS 2.0

    GDALDemRaster will get data from postgresql(postgis 2.0)
    and use GDAL utility to generate a specified type of image.

    The DEM data stored in the database must be using EPSG:4326 and
    the data rendered will be projected to EPSG:3857.

    server
        Server string of postgresql in sqlalchemy format.

    table
        Table name in postgresql where dem data is stored
    """

    def __init__(self, data_type, server='', table=''):
        Cartographer.__init__(self, data_type)

        if self._data_type.name not in ('gtiff'):
            raise TypeError('Only support GTIFF Format.')

        # Create session
        pool_class = sqlalchemy.pool.StaticPool
        engine = sqlalchemy.create_engine(server, poolclass=pool_class)

        self._session_maker = scoped_session(sessionmaker(bind=engine))
        self._table = table

    def doodle(self, envelope=(-180, -90, 180, 90), size=(256, 256)):
        """ Get dem data in the area of envelope from database """

        buffered_envelope = _buffer_envelope(envelope, size, 5)

        bbox_sql = "ST_MakeEnvelope(%f, %f, %f, %f, 4326)" % buffered_envelope
        querysql = DEM_DATA_QUERY % {'bbox': bbox_sql, 'table': self._table}

        try:
            session = self._session_maker()
            row = session.query('dem_data').from_statement(querysql).one()
            data = row.dem_data
            if not data:
                raise ValueError('Empty Data.')

            data_type = self._data_type
            data = gdal_warp(data,
                             envelope=envelope,
                             srs=('EPSG:4326', 'EPSG:3857'),
                             size=size
                             )

            return RenderData(data, data_type)
        finally:
            session.close()
