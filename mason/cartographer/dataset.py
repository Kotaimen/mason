# -*- coding:utf-8 -*-
'''
Created on Oct 12, 2012

@author: ray
'''
import io
import subprocess
from osgeo import gdal, gdalconst

from .cartographer import Cartographer
from .gdaltools import SpatialReference
from .gdalraster import GDALTempFileRaster


class RasterDataset(Cartographer):

    """ Raster Dataset 

    Raster Dataset craft raster data from various raster datasets
    """

    def __init__(self, dataset_path, projection='EPSG:3857', nodata=None):
        Cartographer.__init__(self, 'GTIFF')
        dataset = gdal.Open(dataset_path, gdalconst.GA_ReadOnly)
        if not dataset:
            raise RuntimeError('dataset not found. %s' % dataset_path)

        alignment = dataset.GetGeoTransform()

        # get resolution of dataset
        self._dataset_resx = abs(alignment[1])
        self._dataset_resy = abs(alignment[5])

        # close data
        dataset = None

        self._dataset_path = dataset_path
        self._nodata = nodata

        self._projection = projection
        self._epsg = int(projection.split(':')[1])

    def render(self, envelope=(-180, -90, 180, 90), size=(256, 256)):
        """ Get raster data in the area of envelope from database """

        width, height = size
        proj = self._projection

        srs = SpatialReference(4326, self._epsg)
        minx, miny, maxx, maxy = envelope

        minx, miny, __foo = srs.forward(minx, miny)
        maxx, maxy, __foo = srs.forward(maxx, maxy)

        resx = abs(maxx - minx) / width
        resy = abs(maxy - miny) / height

        # it is better to use cublicspline when stretching out
        if resx < self._dataset_resx and resy < self._dataset_resy:
            resample_method = 'cubic'
        else:
            resample_method = 'cubicspline'

        try:
            target_raster = GDALTempFileRaster(data_format='gtiff')

            command = ['gdalwarp',
                       '-t_srs', proj,
                       '-ts', str(width), str(height),
                       '-dstnodata', str(self._nodata),
                       '-te', str(minx), str(miny), str(maxx), str(maxy),
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
