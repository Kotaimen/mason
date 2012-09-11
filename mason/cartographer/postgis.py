# -*- coding:utf-8 -*-
'''
Get DEM data from PostgreSQL with PostGIS 2.0

Created on May 2, 2012
@author: ray
'''
import io
import sqlalchemy
from sqlalchemy.orm import scoped_session, sessionmaker

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


#==============================================================================
# Base class of GDAL DEM Raster Maker
#==============================================================================
class PostGIS(Cartographer):

    """ Get DEM data from PostgreSQL PostGIS 2.0

    PostGIS takes data from PostgreSQL(PostGIS 2.0).

    server
        Server string of PostgreSQL in SqlAlchemy format.

    table
        Table name in PostgreSQL where DEM data is stored
    """

    def __init__(self, server='', table=''):
        assert server and table
        Cartographer.__init__(self, 'GTIFF')

        # Create session
        pool_class = sqlalchemy.pool.StaticPool
        engine = sqlalchemy.create_engine(server, poolclass=pool_class)

        self._session_maker = scoped_session(sessionmaker(bind=engine))
        self._table = table

    def render(self, envelope=(-180, -90, 180, 90), size=(256, 256)):
        """ Get dem data in the area of envelope from database """

        bbox_stmt = "ST_MakeEnvelope(%f, %f, %f, %f, 4326)" % envelope
        query = DEM_DATA_QUERY % {'bbox': bbox_stmt, 'table': self._table}

        try:
            session = self._session_maker()
            row = session.query('dem_data').from_statement(query).one()
            data = row.dem_data
            if not data:
                raise RuntimeError('No DEM data found with SQL: %s' % query)

            return io.BytesIO(data)
        finally:
            session.close()
