# -*- coding:utf-8 -*-
'''
Get Raster data from PostgreSQL with PostGIS 2.0

Created on May 2, 2012
@author: ray
'''
import io
import sqlalchemy
from sqlalchemy.orm import scoped_session, sessionmaker

from .cartographer import Cartographer
from .gdaltools import GDALRaster, GDALFixMetaData

RASTER_DATA_QUERY = '''
SELECT
ST_AsTIFF(
    ST_Resample(
    ST_UNION(ST_CLIP(rast, %(bbox)s, true)),
    %(width)d,%(height)d,3857,NULL,NULL,0,0,'CubicSpline'
    ),
    ARRAY['PIXELTYPE=SIGNEDBYTE','PROFILE=GeoTIFF'],
    %(proj)d
)
AS raster_data
FROM %(table)s
WHERE ST_INTERSECTS(rast, %(bbox)s)
'''


#==============================================================================
# PostGIS Raster Cartographer
#==============================================================================
class PostGIS(Cartographer):

    """ Get raster data from PostgreSQL PostGIS 2.0

    PostGIS takes data from PostgreSQL(PostGIS 2.0).

    server
        Server string of PostgreSQL in SqlAlchemy format.

    table
        Table name of raster data.
    """

    def __init__(self, server='', table='', projection='EPSG:3857'):
        if not server:
            raise ValueError('invalid server: "%s"' % server)
        if not table:
            raise ValueError('invalid table: "%s"' % table)
        if not projection.startswith('EPSG:'):
            raise ValueError('only support EPSG projection.')

        Cartographer.__init__(self, 'GTIFF')

        # Create session
        pool_class = sqlalchemy.pool.StaticPool
        engine = sqlalchemy.create_engine(server, poolclass=pool_class)

        self._session_maker = scoped_session(sessionmaker(bind=engine))
        self._table = table

        epsg_int = int(projection.split(':')[1])
        self._projection = epsg_int

        self._nodata = -32768

    def render(self, envelope=(-180, -90, 180, 90), size=(256, 256)):
        """ Get raster data in the area of envelope from database """

        width, height = size
        proj = self._projection

        xmin, ymin, xmax, ymax = envelope
        bbox_stmt = "ST_Transform(ST_MakeEnvelope(%f, %f, %f, %f, 4326), %d)" \
                        % (xmin, ymin, xmax, ymax, proj)

        query = RASTER_DATA_QUERY % {'bbox': bbox_stmt,
                                     'table': self._table,
                                     'width': width,
                                     'height': height,
                                     'proj': proj}

        try:
            session = self._session_maker()
            row = session.query('raster_data').from_statement(query).one()
            data = str(row.raster_data)
            if not data:
                raise RuntimeError('No Raster data found with SQL: %s' % query)

            raster = GDALRaster(data, 'GTIFF')
            fixer = GDALFixMetaData(fix_srs=proj, set_nodata=self._nodata)
            output_raster = fixer.convert(raster)

            return io.BytesIO(output_raster.data)
        finally:
            session.close()
