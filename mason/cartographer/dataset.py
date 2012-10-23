# -*- coding:utf-8 -*-
'''
Created on Oct 12, 2012

@author: ray
'''
import io
import subprocess
from osgeo import gdal, gdalconst, osr

from .cartographer import Cartographer
from .gdaltools import SpatialReference
from .gdalraster import GDALTempFileRaster


class RasterDataset(Cartographer):

    """ GDAL Raster Data Source

    Crop envelope and re-projects GDAL data source into target projection,
    output result as GeoTIFF stream.

    Parameters:
    :param dataset_path:
        pathname to GDAL raster file
    :param target_projection:
        target projection in EPSG:XXXX format, default is 'EPSG:3857'
    :param target_nodata:
        nodata value of output raster, by default, uses same value as input
    :param resample_method'
        resampling method, see gdalwrap help for available
        options (near/bilinear/cubic/cubicspline/lanczos as of gdal1.9).  By
        default, this is automatically decided from source and target resultion.
        (cubic while reducing size, cubicspline while enlarging)
    :param work_memory:
        gdal work memory in MB, note value>2000 seems do not
        work properly, default is 128, increase this
        while rendering very large Metatile
    :rtype:
        bytes input stream

    """

    def __init__(self,
                 dataset_path,
                 target_projection='EPSG:3857',
                 target_nodata= -32768,
                 resample_method=None,
                 work_memory=512):
        Cartographer.__init__(self, 'GTIFF')
        dataset = gdal.Open(dataset_path, gdalconst.GA_ReadOnly)
        if not dataset:
            raise RuntimeError('dataset not found. %s' % dataset_path)

        # get dataset information
        alignment = dataset.GetGeoTransform()

        # get resolution of dataset
        self._dataset_resx = abs(alignment[1])
        self._dataset_resy = abs(alignment[5])

        # get projection of dataset
        srs = osr.SpatialReference()
        srs.ImportFromWkt(dataset.GetProjection())
        srs.AutoIdentifyEPSG()
        if srs.IsGeographic():
            epsg = srs.GetAuthorityCode('GEOGCS')
        else:
            epsg = srs.GetAuthorityCode('PROJCS')
        self._dataset_epsg = int(epsg)

        # close data
        dataset = None

        self._dataset_path = dataset_path
        self._target_projection = target_projection
        self._target_nodata = target_nodata
        self._work_mem = work_memory
        self._resample_method = resample_method

        self._target_epsg = int(target_projection.split(':')[1])

    def render(self, envelope=(-180, -90, 180, 90), size=(256, 256)):
        """ Get raster data in the area of envelope from database """

        target_width, target_height = size
        minx, miny, maxx, maxy = envelope

        # calculate envelope coordinates in target projection
        srs = SpatialReference(4326, self._target_epsg)
        dst_minx, dst_miny, __foo = srs.forward(minx, miny)
        dst_maxx, dst_maxy, __foo = srs.forward(maxx, maxy)

        # HACK 1: fix coordinates error
        # otherwise, gdal will project -181 to 19926188.852, which is wrong.
        mark180, __foo, __foo = srs.forward(180, 0)
        if minx < -180:
            assert minx > -360
            dst_minx = -mark180 - (mark180 - dst_minx)
        if maxx > 180:
            assert maxx < 360
            dst_maxx = mark180 + (mark180 + dst_maxx)

        if self._resample_method is not None:
            resample_method = self._resample_method
        else:

            # Choose Resampling Method:
            # Forward coordinates of input envelop, which is in WGS84, to
            # the corresponding coordinates in Dataset projection.
            # Original Raster size in Dataset projection can be calculated by that
            # coordinates and the resolution of Dataset.
            # Cubicspline works better when stretching out (target size is
            # larger than the original size). And Cubic results better image on the
            # opposite condition.

            # calculate envelope coordinates in dataset projection
            srs = SpatialReference(4326, self._dataset_epsg)
            org_minx, org_miny, __foo = srs.forward(minx, miny)
            org_maxx, org_maxy, __foo = srs.forward(maxx, maxy)

            org_width = abs(org_minx - org_maxx) / self._dataset_resx
            org_height = abs(org_maxy - org_miny) / self._dataset_resy
            if target_width < org_width and target_height < org_height:
                resample_method = 'cubic'
            else:
                resample_method = 'cubicspline'

        try:
            target_raster = GDALTempFileRaster(data_format='gtiff')

            command = ['gdalwarp',
                       '-ts', str(target_width), str(target_height),
                       '-dstnodata', str(self._target_nodata),
                       '-te', str(dst_minx), str(dst_miny),
                              str(dst_maxx), str(dst_maxy),
                       '-r', resample_method,
                       '-wm', str(int(self._work_mem)),
                       '-overwrite',
                       '-of', 'gtiff',
                       '-q',
                       ]

            if self._dataset_epsg != self._target_epsg:
                command.extend(['-t_srs', self._target_projection])

                # HACK 2:
                # GDAL transforms the destination area
                # back to the source coordinate system by sampling
                # a grid of points over the region.
                # But points right on the international date line might
                # transform two different ways.
                # so the region selector is missing the last swath of
                # data.
                # Setting source_extra will read more data from the source.
                source_extra = 1
                if minx <= -180 or maxx >= 180:
                    source_extra = target_width / 2
                command.extend(['-wo', 'SOURCE_EXTRA=%d' % source_extra])

            command.extend([self._dataset_path, target_raster.filename])

            popen = subprocess.Popen(command)
            popen.communicate()

            target_raster.load()
            return io.BytesIO(target_raster.data)

        finally:
            target_raster.close()
