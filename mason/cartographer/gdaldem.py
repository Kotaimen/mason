'''
Created on May 2, 2012

@author: ray
'''
import sqlalchemy
from sqlalchemy.orm import scoped_session, sessionmaker

from ..utils.gdalutil import gdal_warp
from ..core import RenderData
from .cartographer import Cartographer


DEM_DATA_QUERY = """
SELECT
ST_ASGDALRASTER(
ST_UNION(ST_CLIP(the_rast, %(bbox)s, true)), 'GTIFF')
AS dem_data
FROM %(table)s
WHERE ST_INTERSECTS(the_rast, %(bbox)s)
"""


#==============================================================================
# Base class of GDAL DEM Raster Maker
#==============================================================================
class DEMRaster(Cartographer):

    """ GDAL raster maker

    GDALDemRaster will get data from postgresql(postgis 2.0)
    and use gdal utility to generate a specified type of image.

    The dem data stored in database must be in EPSG:4326 and
    The data retrieved will be projected to EPSG:3857.(GOOGLE MERCATOR)

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

        bbox_sql = "ST_MakeEnvelope(%f, %f, %f, %f, 4326)" % envelope
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
