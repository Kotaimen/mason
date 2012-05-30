'''
Created on May 2, 2012

@author: ray
'''
import os
import tempfile
import sqlalchemy
from sqlalchemy.orm import scoped_session, sessionmaker

from ..core import RenderData
from .cartographer import Raster
from .gdalutil import gdal_hillshade, gdal_colorrelief, gdal_warp
from .errors import GDALTypeError, GDALDataError


DEM_DATA_QUERY = """
SELECT
ST_ASGDALRASTER(
ST_UNION(ST_CLIP(the_rast, %(bbox)s, true)), 'GTIFF')
AS dem_data
FROM %(table)s
WHERE ST_INTERSECTS(the_rast, %(bbox)s)
"""


#==============================================================================
# Helper Functions
#==============================================================================
def _buffer_envelope(envelope, size, buffer_size):
    """ Buffer the envelope with buffer_size(pixel size)

    This is an approximate approach that makes the given envelope a
    little bigger than its original size.

    Buffer is calculated by:
        Buffer Degree = Degree_Diff / Pixel_Diff * Buffer_Pixel

    This should be improved if any efficient method is found in the future.
    """
    width, height = size
    minx, miny, maxx, maxy = envelope

    diff_x = abs(maxx - minx)
    diff_y = abs(maxy - miny)

    buffer_x = diff_x / width * buffer_size
    buffer_y = diff_y / height * buffer_size

    new_envelope = (minx - buffer_x,
                    miny - buffer_y,
                    maxx + buffer_x,
                    maxy + buffer_y,
                    )
    return new_envelope


def _get_tmp_file(tag):
    """ Create a temporary file  """
    suffix = '_%d_%s' % (os.getpid(), tag)
    fd, tmpname = tempfile.mkstemp(suffix=suffix,
                                   dir=tempfile.gettempdir(),
                                   text=False)
    return fd, tmpname


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
        Server string of postgresql in sqlalchemy format.

    dem_table
        Table name in postgresql where dem data is stored

    image_type
        Type of output image

    image_parameters
        A dictionary of parameters of image
    """

    def __init__(self,
                 server='',
                 pool_size=5,
                 dem_table='',
                 data_type=None
                 ):
        Raster.__init__(self, data_type)

        if self._data_type.name not in ('gtiff', 'png', 'jpeg'):
            raise GDALTypeError('Only support GTIFF/PNG/JPEG Format.')

        # Create session
        engine = sqlalchemy.create_engine(
                        server,
                        poolclass=sqlalchemy.pool.StaticPool,
#                        pool_size=pool_size
                        )

        self._session_maker = scoped_session(sessionmaker(bind=engine))
        self._table = dem_table

    def get_dem_data(self, envelope):
        """ Get dem data in the area of envelope from database """

        bbox_sql = "ST_MakeEnvelope(%f, %f, %f, %f, 4326)" % envelope
        querysql = DEM_DATA_QUERY % {'bbox': bbox_sql, 'table': self._table}

        try:
            session = self._session_maker()
            row = session.query('dem_data').from_statement(querysql).one()
            session.close()
            data = row.dem_data
            if not data:
                raise GDALDataError('Empty Data.')
            return data
        except Exception as e:
            session.rollback()
            raise GDALDataError('No Dem Data Found. %s' % str(e))

    def doodle(self, envelope=(-180, -90, 180, 90), size=(256, 256)):
        raise NotImplementedError


#==============================================================================
# Hill shade maker
#==============================================================================
class GDALHillShade(GDALDEMRaster):

    """ Make Hill Shade

    zfactor
        Vertical scale factor.

    scale
        Horizontal scale factor:
        Feet:Latlong     scale=370400
        Meter:LatLong    scale=111120

    azimuth
        Azimuth of the light.

    altitude
        Altitude of the light, in degrees.

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
                 data_type=None
                 ):

        GDALDEMRaster.__init__(self,
                               server=server,
                               pool_size=pool_size,
                               dem_table=dem_table,
                               data_type=data_type
                               )

        if data_type.name not in ['gtiff']:
            raise GDALTypeError('Hillshade only support gtiff output.')

        self._zfactor = zfactor
        self._scale = scale
        self._azimuth = azimuth
        self._altitude = altitude

    def doodle(self, envelope=(-180, -90, 180, 90), size=(256, 256)):

        # HACK: Buffer 5 pixel to render a larger image.
        # We buffered a little first and crop the image back to the original
        # envelope in order to eliminate boundaries around the selected data
        # from PostGIS (Boundary sucks...Any good idea?).
        #
        # GDAL <=1.7 do not support '-compute_edges',
        # without which there will be back boundaries around generated
        # hill shade or color-relief as well.

        buffered = _buffer_envelope(envelope, size, 5)
        dem_data = self.get_dem_data(buffered)

        try:
            # GDAL only support file as their input and output.
            fd1, src_tempname = _get_tmp_file('hillshade_src')
            fd2, wrp_tempname = _get_tmp_file('hillshade_wrp')
            fd3, dst_tempname = _get_tmp_file('hillshade_dst')

            os.close(fd1)
            os.close(fd2)
            os.close(fd3)

            # write dem data to temp file
            with open(src_tempname, 'wb') as fp:
                fp.write(dem_data)

            # create hill shade
            data_type = self._data_type
            gdal_hillshade(src_tempname,
                           wrp_tempname,
                           self._zfactor,
                           self._scale,
                           self._azimuth,
                           self._altitude
                           )

            # warp to size
            gdal_warp(wrp_tempname,
                      dst_tempname,
                      envelope=envelope,
                      srs=('EPSG:4326', 'EPSG:3857'),
                      size=size)

            # get result data from temporary file
            with open(dst_tempname, 'rb') as fp:
                data = fp.read()

            return RenderData(data, data_type)

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
        A text file with the following format
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
                 data_type=None
                 ):
        GDALDEMRaster.__init__(self,
                               server=server,
                               pool_size=pool_size,
                               dem_table=dem_table,
                               data_type=data_type)

        self._color_context = color_context

    def doodle(self, envelope=(-180, -90, 180, 90), size=(256, 256)):
        # Please refer to the comment for Hillshade.
        buffered = _buffer_envelope(envelope, size, 5)
        dem_data = self.get_dem_data(buffered)

        try:
            # gdal utilities only support file as their input and output.
            fd1, src_tempname = _get_tmp_file('colorrelief_src')
            fd2, wrp_tempname = _get_tmp_file('colorrelief_wrp')
            fd3, dst_tempname = _get_tmp_file('colorrelief_dst')

            os.close(fd1)
            os.close(fd2)
            os.close(fd3)

            # write dem data to temporary file
            with open(src_tempname, 'wb') as fp:
                fp.write(dem_data)

            # warp to size
            gdal_warp(src_tempname,
                      wrp_tempname,
                      envelope=envelope,
                      srs=('EPSG:4326', 'EPSG:3857'),
                      size=size)

            data_type = self._data_type
            gdal_colorrelief(wrp_tempname,
                             dst_tempname,
                             self._color_context,
                             data_type.name,
                             data_type.parameters
                            )

            # get result data from temporary file
            with open(dst_tempname, 'rb') as fp:
                data = fp.read()

            return RenderData(data, data_type)

        finally:
            os.remove(src_tempname)
            os.remove(dst_tempname)
            os.remove(wrp_tempname)
