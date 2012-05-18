'''
Created on May 2, 2012

@author: ray
'''
import os
import tempfile
import sqlalchemy
from sqlalchemy.orm import scoped_session, sessionmaker

from .cartographer import Raster
from .gdalutil import gdal_hillshade, gdal_colorrelief, gdal_warp
from .errors import GDALTypeError, GDALDataError


#==============================================================================
# Base class of GDAL DEM Raster Maker
#==============================================================================
class GDALDEMRaster(Raster):

    """ GDAL raster maker

    GDALDemRaster will get data from postgresql(postgis 2.0)
    and use gdal utility to generate a specified type of image.

    The dem data stored in database must be in EPSG:4326 and
    The data retrieved will be projected to EPSG:3857.(GOOGLE MERCATOR)

    server
        server string of postgresql in sqlalchemy format.

    dem_table
        table name in postgresql where dem data is stored

    image_type
        type of output image

    image_parameters
        a dictionary of parameters of image
    """

    def __init__(self,
                 server='',
                 pool_size=10,
                 dem_table='',
                 image_type='gtiff',
                 image_parameters=None,
                 ):
        Raster.__init__(self, image_type, image_parameters)

        # Create session
        engine = sqlalchemy.create_engine(
                        server,
                        poolclass=sqlalchemy.pool.SingletonThreadPool,
                        pool_size=pool_size)

        self._session_maker = scoped_session(sessionmaker(bind=engine))
        self._table = dem_table

    def get_dem_data(self, envelope):
        """ Get dem data in the area of envelope from database """

        bbox_sql = "ST_MakeEnvelope(%f, %f, %f, %f, 4326)" % envelope

        sql = """ SELECT
                      ST_ASGDALRASTER(
                          ST_TRANSFORM(
                              ST_UNION(
                                  ST_CLIP(the_rast, %(bbox)s, true)
                              ),
                              3857,
                              'Cubic'
                          ),
                          'GTiff'
                      ) AS dem_data
                  FROM %(table)s
                  WHERE ST_INTERSECTS(the_rast, %(bbox)s)
              """ % {'bbox': bbox_sql,
                     'table': self._table}

        sql = sql.replace('\n', ' ')

        session = self._session_maker()
        try:
            row = session.query('dem_data').from_statement(sql).one()
            session.close()
            data = row.dem_data
            if not data:
                raise GDALDataError('Empty Data.')
            return data
        except Exception as e:
            session.rollback()
            raise GDALDataError('No Dem Data Found. %s' % str(e))

    def doodle(self, envelope=(-180, -85, 180, 85), size=(256, 256)):
        """ Make raster image of a specified envelope """
        raise NotImplementedError

    def close(self):
        pass

    def _get_tmp_file(self, tag):
        suffix = '_%d_%s' % (os.getpid(), tag)
        fd, tmpname = tempfile.mkstemp(suffix=suffix,
                                       dir=tempfile.gettempdir(),
                                       text=False)
        return fd, tmpname


#==============================================================================
# Hill shade maker
#==============================================================================
class GDALHillShade(GDALDEMRaster):

    """ Make Hill Shade

    zfactor
        vertical scale factor.

    scale
        horizontal scale factor:
            feet:Latlong use scale=370400
            Meters:LatLong use scale=111120

    azimuth
        azimuth of the light.

    altitude
        altitude of the light, in degrees.

    image_type
        GTIFF is supported ONLY currently
    """

    def __init__(self,
                 zfactor=2,
                 scale=1,
                 azimuth=315,
                 altitude=45,
                 server='',
                 pool_size=10,
                 dem_table='',
                 image_type='gtiff',
                 image_parameters=None,
                 ):

        GDALDEMRaster.__init__(self,
                               server=server,
                               pool_size=pool_size,
                               dem_table=dem_table,
                               image_type=image_type,
                               image_parameters=image_parameters)

        self._zfactor = zfactor
        self._scale = scale
        self._azimuth = azimuth
        self._altitude = altitude

        if self._image_type not in ('gtiff', 'png', 'jpeg'):
            raise GDALTypeError('Hill Shade Only support GTIFF, PNG, JPEG.')

    def doodle(self, envelope=(-180, -85, 180, 85), size=(256, 256)):

        dem_data = self.get_dem_data(envelope)

        try:
            # GDAL only support file as their input and output.
            _fd, src_tempname = self._get_tmp_file('hillshade_src')
            _fd, wrp_tempname = self._get_tmp_file('hillshade_wrp')
            _fd, dst_tempname = self._get_tmp_file('hillshade_dst')

            # write dem data to temp file
            with open(src_tempname, 'wb') as fp:
                fp.write(dem_data)

            # warp to size
            width, height = size
            gdal_warp(src_tempname, wrp_tempname, width, height)

            # create hill shade
            gdal_hillshade(wrp_tempname,
                           dst_tempname,
                           self._zfactor,
                           self._scale,
                           self._azimuth,
                           self._altitude,
                           self._image_type,
                           self._image_parameters)

            # get result data from temp file
            with open(dst_tempname, 'rb') as fp:
                data = fp.read()

            return data

        finally:
            os.remove(src_tempname)
            os.remove(dst_tempname)
            os.remove(wrp_tempname)


#==============================================================================
# Color relief Maker
#==============================================================================
class GDALColorRelief(GDALDEMRaster):

    """ Make color relief

    color_context
        a text file with the following format
            3500   white
            2500   235:220:175
            50%    190 185 35
            700    240 250 150
            0      50  180 50
            nv     0   0   0      #nv: no data value

    """

    def __init__(self,
                 color_context=None,
                 server='',
                 pool_size=10,
                 dem_table='',
                 image_type='gtiff',
                 image_parameters=None,
                 ):
        GDALDEMRaster.__init__(self,
                               server=server,
                               pool_size=pool_size,
                               dem_table=dem_table,
                               image_type=image_type,
                               image_parameters=image_parameters)

        self._color_context = color_context

        if self._image_type not in ('gtiff', 'png', 'jpeg'):
            raise GDALTypeError('Hill Shade Only support GTIFF, PNG, JPEG.')

    def doodle(self, envelope=(-180, -85, 180, 85), size=(256, 256)):

        dem_data = self.get_dem_data(envelope)

        try:
            # gdal utilities only support file as their input and output.
            _fd, src_tempname = self._get_tmp_file('colorrelief_src')
            _fd, wrp_tempname = self._get_tmp_file('colorrelief_wrp')
            _fd, dst_tempname = self._get_tmp_file('colorrelief_dst')

            # write dem data to temp file
            with open(src_tempname, 'wb') as fp:
                fp.write(dem_data)

            # warp to size
            width, height = size
            gdal_warp(src_tempname, wrp_tempname, width, height)

            gdal_colorrelief(wrp_tempname,
                             dst_tempname,
                             self._color_context,
                             self._image_type,
                             self._image_parameters
                            )

            # get result data from temp file
            with open(dst_tempname, 'rb') as fp:
                data = fp.read()

            return data

        finally:
            os.remove(src_tempname)
            os.remove(dst_tempname)
            os.remove(wrp_tempname)
