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

    """ Raster Dataset

    Raster Dataset craft raster data from various raster datasets
    """

    def __init__(self,
                 dataset_path,
                 target_projection='EPSG:3857',
                 target_nodata=None,
                 work_mem=128):
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

        self._target_epsg = int(target_projection.split(':')[1])

    def render(self, envelope=(-180, -90, 180, 90), size=(256, 256)):
        """ Get raster data in the area of envelope from database """

        target_width, target_height = size
        minx, miny, maxx, maxy = envelope

        # calculate envelope coordinates in target projection
        srs = SpatialReference(4326, self._target_epsg)
        dst_minx, dst_miny, __foo = srs.forward(minx, miny)
        dst_maxx, dst_maxy, __foo = srs.forward(maxx, maxy)

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

        # it is better to use cublicspline when stretching out
        if target_width < org_width and target_height < org_height:
            resample_method = 'cubic'
        else:
            resample_method = 'cubicspline'

        try:
            target_raster = GDALTempFileRaster(data_format='gtiff')

            command = ['gdalwarp',
                       '-t_srs', self._target_projection,
                       '-ts', str(target_width), str(target_height),
                       '-dstnodata', str(self._target_nodata),
                       '-te', str(dst_minx), str(dst_miny), str(dst_maxx), str(dst_maxy),
                       '-r', resample_method,
                       '-wm', '128',
                       '-overwrite',
                       '-of', 'gtiff',
                       '-q',
                       self._dataset_path,
                       target_raster.filename
                       ]

            popen = subprocess.Popen(command)
            popen.communicate()

            target_raster.load()
            return io.BytesIO(target_raster.data)

        finally:
            target_raster.close()
