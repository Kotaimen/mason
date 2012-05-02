'''
Created on May 2, 2012

@author: ray
'''
import os
import tempfile
import sqlalchemy

from .cartographer import Raster
from .gdalutil import gdal_hillshade, gdal_colorrelief
from .errors import GDALError, GDALTypeError

def get_pool_class(class_name):
    POOLS = {'QueuePool': sqlalchemy.pool.QueuePool,
             'SingletonThreadPool': sqlalchemy.pool.SingletonThreadPool,
             'StaticPool': sqlalchemy.pool.StaticPool}
    return POOLS[class_name]


#===============================================================================
# Base class of GDAL DEM Raster Maker
#===============================================================================
class GDALDEMRaster(Raster):

    """ GDAL raster maker
    
    Retrieve data from postgresql database with postgis 2.0,
    and render to specified type.
    """

    def __init__(self,
                 server='',
                 pool_class='QueuePool',
                 pool_size=5,
                 pool_parameters=None,
                 dialect_parameters=None,
                 image_type='png',
                 image_parameters=None,
                 ):
        Raster.__init__(self, image_type, image_parameters)

        engine_parameters = dict(poolclass=pool_class,
                                 pool_size=pool_size,)

        if pool_parameters:
            engine_parameters.update(pool_parameters)

        if dialect_parameters:
            engine_parameters.update(dialect_parameters)

        self._engine = sqlalchemy.create_engine(server, **engine_parameters)

        self._session_maker = sqlalchemy.orm.sessionmaker(bind=self._engine)
        self._metadata = sqlalchemy.MetaData(bind=self._engine)
        self._pool = self._engine

    def make(self, envelop=(-180, -85, 180, 85), size=(256, 256)):
        # get projected data in the envelop
        # process data
        # return 
        raise NotImplementedError

    def _get_dem_data(self):
        raise NotImplementedError

#===============================================================================
# Hill shade maker
#===============================================================================
class GDALHillShade(GDALDEMRaster):

    def __init__(self,
                 zfactor=2,
                 scale=1,
                 azimuth=315,
                 altitude=45,
                 server='',
                 pool_class='QueuePool',
                 pool_size=5,
                 pool_parameters=None,
                 dialect_parameters=None,
                 image_type='png',
                 image_parameters=None,
                 ):
        GDALDEMRaster.__init__(self,
                            server,
                            pool_class,
                            pool_size,
                            pool_parameters,
                            dialect_parameters,
                            image_type,
                            image_parameters)

        self._zfactor = zfactor
        self._scale = scale
        self._azimuth = azimuth
        self._altitude = altitude

        if image_type != 'png':
            raise GDALTypeError('Hill Shade Only support PNG output.')

    def make(self, envelop=(-180, -85, 180, 85), size=(256, 256)):

        dem_data = self._get_dem_data()

        try:
            # write dem data to temporary file
            # gdal utilities only support file as their input and output.
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file.write(dem_data)
            temp_file.close()

            ext = self._image_type
            src_file_path = temp_file.name
            dst_file_path = src_file_path + '_hillshade' + '.' + ext

            gdal_hillshade(src_file_path,
                           dst_file_path,
                           self._zfactor,
                           self._scale,
                           self._azimuth,
                           self._altitude)

            with open(dst_file_path, 'r') as fp:
                data = fp.read()

            return data

        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            if os.path.exists(dst_file_path):
                os.remove(dst_file_path)



#===============================================================================
# Color relief Maker
#===============================================================================
class GDALColorRelief(GDALDEMRaster):

    def __init__(self,
                 color_context=None,
                 server='',
                 pool_class='QueuePool',
                 pool_size=5,
                 pool_parameters=None,
                 dialect_parameters=None,
                 image_type='png',
                 image_parameters=None,
                 ):
        GDALDEMRaster.__init__(self,
                            server,
                            pool_class,
                            pool_size,
                            pool_parameters,
                            dialect_parameters,
                            image_type,
                            image_parameters)

        self._color_context = color_context
        if image_type != 'png':
            raise GDALTypeError('Color relief Only support PNG output.')


    def make(self, envelop=(-180, -85, 180, 85), size=(256, 256)):
        dem_data = self._get_dem_data()

        try:
            # write dem data to temporary file
            # gdal utilities only support file as their input and output.
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file.write(dem_data)
            temp_file.close()

            ext = self._image_type
            src_file_path = temp_file.name
            dst_file_path = src_file_path + '_colorrelief' + '.' + ext

            gdal_hillshade(src_file_path,
                           dst_file_path,
                           self._color_context
                           )

            with open(dst_file_path, 'r') as fp:
                data = fp.read()

            return data

        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            if os.path.exists(dst_file_path):
                os.remove(dst_file_path)
