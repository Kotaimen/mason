'''
Created on May 2, 2012

@author: ray
'''
import os
import tempfile
import sqlalchemy

from .cartographer import Raster
from .gdalutil import gdal_hillshade, gdal_colorrelief
from .errors import GDALTypeError


#==============================================================================
# Base class of GDAL DEM Raster Maker
#==============================================================================
class GDALDEMRaster(Raster):

    """ GDAL raster maker

    Retrieve data from postgresql database with postgis 2.0,
    and render to specified type.
    """

    def __init__(self,
                 server='',
                 image_type='png',
                 image_parameters=None,
                 ):
        Raster.__init__(self, image_type, image_parameters)

        # Singleton Thread Pool with pool size=1 (For process model)
        engine_parameters = dict(poolclass=sqlalchemy.pool.SingletonThreadPool,
                                 pool_size=1,)

        self._engine = sqlalchemy.create_engine(server, **engine_parameters)

        self._session_maker = sqlalchemy.orm.sessionmaker(bind=self._engine)
        self._metadata = sqlalchemy.MetaData(bind=self._engine)
        self._pool = self._engine

    def make(self, envelope=(-180, -85, 180, 85), size=(256, 256)):
        raise NotImplementedError

    def _get_dem_data(self):
        raise NotImplementedError

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

    def __init__(self,
                 zfactor=2,
                 scale=1,
                 azimuth=315,
                 altitude=45,
                 server='',
                 image_type='png',
                 image_parameters=None,
                 ):
        GDALDEMRaster.__init__(self,
                            server,
                            image_type,
                            image_parameters)

        self._zfactor = zfactor
        self._scale = scale
        self._azimuth = azimuth
        self._altitude = altitude

        if image_type != 'png':
            raise GDALTypeError('Hill Shade Only support PNG output.')

    def make(self, envelope=(-180, -85, 180, 85), size=(256, 256)):

        dem_data = self._get_dem_data()

        try:
            # write dem data to temporary file
            # gdal utilities only support file as their input and output.
            _fd, src_tempname = self._get_tmp_file('hillshade_src')
            _fd, dst_tempname = self._get_tmp_file('hillshade_dst')

            # write dem data to temp file
            with open(src_tempname, 'wb') as fp:
                fp.write(dem_data)

            gdal_hillshade(src_tempname,
                           dst_tempname,
                           self._zfactor,
                           self._scale,
                           self._azimuth,
                           self._altitude)

            # get result data from temp file
            with open(dst_tempname, 'rb') as fp:
                data = fp.read()

            return data

        finally:
            os.remove(src_tempname)
            os.remove(dst_tempname)


#==============================================================================
# Color relief Maker
#==============================================================================
class GDALColorRelief(GDALDEMRaster):

    def __init__(self,
                 color_context=None,
                 server='',
                 image_type='png',
                 image_parameters=None,
                 ):
        GDALDEMRaster.__init__(self,
                               server,
                               image_type,
                               image_parameters)

        self._color_context = color_context

        if image_type != 'png':
            raise GDALTypeError('Color relief Only support PNG output.')

    def make(self, envelope=(-180, -85, 180, 85), size=(256, 256)):

        dem_data = self._get_dem_data()

        try:
            # write dem data to temporary file
            # gdal utilities only support file as their input and output.
            _fd, src_tempname = self._get_tmp_file('colorrelief_src')
            _fd, dst_tempname = self._get_tmp_file('colorrelief_dst')

            # write dem data to temp file
            with open(src_tempname, 'wb') as fp:
                fp.write(dem_data)

            gdal_colorrelief(src_tempname,
                             dst_tempname,
                             self._color_context
                            )

            # get result data from temp file
            with open(dst_tempname, 'rb') as fp:
                data = fp.read()

            return data

        finally:
            os.remove(src_tempname)
            os.remove(dst_tempname)
