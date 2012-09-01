# -*- coding:utf-8 -*-
'''
Created on Aug 30, 2012

@author: ray
'''
import subprocess
from osgeo import osr

from ..core.format import Format
from .gdalraster import GDALTempFileRaster


class SpatialReference(object):

    def __init__(self, src_epsg, dst_epsg, place=12):
        assert isinstance(src_epsg, int)
        assert isinstance(dst_epsg, int)

        src_srs = osr.SpatialReference()
        src_srs.ImportFromEPSG(src_epsg)

        dst_srs = osr.SpatialReference()
        dst_srs.ImportFromEPSG(dst_epsg)

        self._forward = osr.CoordinateTransformation(src_srs, dst_srs)
        self._reverse = osr.CoordinateTransformation(dst_srs, src_srs)

        # preserve one more digit
        self._round_digit = place + 1

    def forward(self, x, y, z=0):
        x, y, z = self._forward.TransformPoint(x, y, z)
        x = round(x, self._round_digit)
        y = round(y, self._round_digit)
        z = round(z, self._round_digit)
        return (x, y, z)

    def reverse(self, x, y, z=0):
        x, y, z = self._reverse.TransformPoint(x, y, z)
        x = round(x, self._round_digit)
        y = round(y, self._round_digit)
        z = round(z, self._round_digit)
        return (x, y, z)


class GDALRaster(object):

    def __init__(self,
                 filename=None,
                 raster_format=None,
                 raster_data=None):
        self._filename = filename
        self._format = raster_format
        self._data = raster_data

    @property
    def filename(self):
        return self._filename

    @property
    def data(self):
        return self._data

    @property
    def format(self):
        return self._format

    def close(self):
        pass


def _subprocess_call(command_list):
    return subprocess.check_call(command_list) == 0


class GDALProcess(object):

    def __init__(self):
        # default format for both input and output
        self._accept_format = Format.GTIFF
        self._expect_format = Format.GTIFF

    def convert(self, raster):
        assert raster.format is self._accept_format

        # input and output rasters
        source_raster = GDALTempFileRaster(data_format=self._accept_format)
        target_raster = GDALTempFileRaster(data_format=self._expect_format)
        # save data to the temporary file
        source_raster.save(raster.data)

        # process the data
        try:
            self._do_process(source_raster.filename, target_raster.filename)
            # load data from temporary file
            target_raster.load()

            # create output raster
            output = GDALRaster(target_raster.data, target_raster.data_format)
        finally:
            source_raster.close()
            target_raster.close()

        return output

    def _do_process(self, source_file, target_file):
        raise NotImplementedError


class GDALHillShading(GDALProcess):

    def __init__(self, zfactor, scale, altitude, azimuth):
        GDALProcess.__init__(self)
        self._zfactor = str(zfactor)
        self._scale = str(scale)
        self._altitude = str(altitude)
        self._azimuth = str(azimuth)

    def _do_process(self, source_file, target_file):
        command_list = ['gdaldem', 'hillshade',
                        # input and output
                        source_file, target_file,

                        # parameters
                        '-z', self._zfactor,
                        '-s', self._scale,
                        '-alt', self._altitude,
                        '-az', self._azimuth,

                        # compute pixel on edges
                        '-compute_edges',
                        # quite mode
                        '-q',
                       ]
        _subprocess_call(command_list)


class GDALColorRelief(GDALProcess):

    def __init__(self, color_context):
        GDALProcess.__init__(self)
        self._color_context = color_context

    def _do_process(self, source_file, target_file):
        command_list = ['gdaldem', 'color-relief',
                        # input and output
                        source_file,
                        self._color_context,
                        target_file,

                        # add an alpha channel
                        '-alpha',
                        # quite mode
                        '-q'
                        ]
        _subprocess_call(command_list)


class GDALRasterToPNG(GDALProcess):

    def __init__(self):
        GDALProcess.__init__(self)
        self._to_format = Format.PNG

    def _do_process(self, source_file, target_file):
        command_list = ['gdal_translate',
                        '-of', 'PNG',
                        source_file,
                        target_file,
                        ]
        _subprocess_call(command_list)


class GDALRasterMetaData(GDALProcess):

    def __init__(self, to_srs=None,
                       to_envelope=None,
                       to_tiled=False,
                       to_compressed=False,
                       nodata=None):
        self._to_srs = to_srs
        self._to_envelope = to_envelope
        self._to_tiled = to_tiled
        self._to_compressed = to_compressed
        self._nodata = str(nodata)

    def _do_process(self, source_file, target_file):
        command_list = ['gdal_translate',
                        # set parameters
                        '-a_srs', self._to_srs,
                        '-a_ullr', self._to_envelope,
                        '-a_nodata', self._nodata,

                        # input and output
                        source_file,
                        target_file,
                        ]

        _subprocess_call(command_list)


class GDALWarper(GDALProcess):

    def __init__(self, src_epsg, dst_epsg):
        GDALProcess.__init__(self)
        assert isinstance(src_epsg, int)
        assert isinstance(dst_epsg, int)
        self._src_srs = 'EPSG:%d' % src_epsg
        self._dst_srs = 'EPSG:%d' % dst_epsg

    def _do_process(self, source_file, target_file):
        command_list = ['gdalwarp',
                        # parameters
                        '-s_srs', self._src_srs,
                        '-t_srs', self._dst_srs,

                        # set work memory to 512M, default is small
                        '-wm', '512M',
                        # enable multi-threaded
                        '-multi',
                        # quite mode
                        '-q',

                        # input and output
                        source_file,
                        target_file,
                        ]
        _subprocess_call(command_list)
