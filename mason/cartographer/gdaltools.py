# -*- coding:utf-8 -*-
'''
Wrapper for GDAL tools

Created on Aug 30, 2012
@author: ray
'''
import re
import os
import subprocess
from osgeo import osr

from .gdalraster import GDALRaster, GDALTempFileRaster

try:
    stdout = subprocess.Popen(['gdalwarp', '--version'],
                              stdout=subprocess.PIPE).communicate()[0]
except OSError:
    raise ImportError("Can't find gdalwarp, please install GDAL")
gdal_version = float(re.search(r'^GDAL (\d\.\d)\.\d', stdout).group(1))
if gdal_version < 1.8:
    raise ImportError('Requires gdal 1.8 or later')


#==============================================================================
# Spatial Reference Converter
#==============================================================================
class SpatialReference(object):

    """ A spatial reference system converter

    Convert coordinates between different spatial reference system.
    Spatial reference system can be designated by EPSG code.

    src_epsg:
        source spatial reference system in EPSG.

    dst_epsg:
        target spatial reference system in EPSG.

    place:
        valid digit number. no more than 15.

    """

    def __init__(self, src_epsg, dst_epsg, place=12):
        """ create a converter """
        assert isinstance(src_epsg, int)
        assert isinstance(dst_epsg, int)
        assert place < 15

        src_srs = osr.SpatialReference()
        src_srs.ImportFromEPSG(src_epsg)

        dst_srs = osr.SpatialReference()
        dst_srs.ImportFromEPSG(dst_epsg)

        self._forward = osr.CoordinateTransformation(src_srs, dst_srs)
        self._reverse = osr.CoordinateTransformation(dst_srs, src_srs)

        # preserve one more digit
        self._round_digit = place + 1

    def forward(self, x, y, z=0):
        """ convert srs of coordinates from source to target """
        x, y, z = self._forward.TransformPoint(x, y, z)
        x = round(x, self._round_digit)
        y = round(y, self._round_digit)
        z = round(z, self._round_digit)
        return (x, y, z)

    def reverse(self, x, y, z=0):
        """ convert srs of coordinates from target to source """
        x, y, z = self._reverse.TransformPoint(x, y, z)
        x = round(x, self._round_digit)
        y = round(y, self._round_digit)
        z = round(z, self._round_digit)
        return (x, y, z)


#==============================================================================
# GDAL Processors
#==============================================================================
def _subprocess_call(command_list):
    return subprocess.check_call(command_list) == 0


class GDALProcessor(object):

    """ Base Class of GDAL processors

    A template class that holds the procedure of GDAL processing.
    Dedicated GDAL processors will derive from this base class
    and override the _do_process function.
    """

    def __init__(self):
        # default format for both input and output
        self._process_type = ''
        self._accept_format = 'GTIFF'
        self._expect_format = 'GTIFF'

    def convert(self, raster):
        """ convert the raster """
        assert raster.data_format == self._accept_format

        # input and output rasters
        source_raster = GDALTempFileRaster(data_format=self._accept_format,
                                           prefix=self._process_type)
        target_raster = GDALTempFileRaster(data_format=self._expect_format,
                                           prefix=self._process_type)
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
        """ GDAL commands """
        raise NotImplementedError


class GDALHillShading(GDALProcessor):

    """ HillShading Processor

    zfactor:
        vertical exaggeration used to pre-multiply the elevations

    scale:
        ratio of vertical units to horizontal.
        Feet:Latlong use scale=370400
        Meters:LatLong use scale=111120

    azimuth:
        azimuth of the light.

    altitude:
        altitude of the light, in degrees.

    """

    def __init__(self, zfactor=1, scale=1, altitude=45, azimuth=315):
        GDALProcessor.__init__(self)
        self._process_type = 'hillshading'
        assert isinstance(zfactor, int) or isinstance(zfactor, float)
        assert isinstance(scale, int)
        assert isinstance(altitude, int)
        assert isinstance(azimuth, int)

        # set parameters
        self._parameter_list = [
                                # shading parameters
                                '-z', str(zfactor),
                                '-s', str(scale),
                                '-alt', str(altitude),
                                '-az', str(azimuth),

                                # compute pixel on edges
                                '-compute_edges',
                                # quite mode
                                '-q',
                                ]

    def _do_process(self, source_file, target_file):
        command_list = ['gdaldem', 'hillshade',
                        # input and output
                        source_file, target_file,
                       ]
        command_list.extend(self._parameter_list)
        _subprocess_call(command_list)


class GDALColorRelief(GDALProcessor):

    """ Color-relief Processor

    color_context:
        text file with the following format (nv: no data value):
            3500   white
            2500   235:220:175
            50%    190 185 135
            700    240 250 150
            0      50  180  50
            nv     0   0   0

    """

    def __init__(self, color_context):
        GDALProcessor.__init__(self)
        self._process_type = 'colorrelief'

        if not os.path.exists(color_context):
            raise Exception('Color context not found %s' % color_context)

        # set parameters
        self._parameter_list = [
                                # add an alpha channel
                                '-alpha',
                                # quite mode
                                '-q'
                                ]
        self._color_context = color_context

    def _do_process(self, source_file, target_file):
        command_list = ['gdaldem', 'color-relief',
                        # input and output
                        source_file,
                        self._color_context,
                        target_file,
                        ]
        command_list.extend(self._parameter_list)
        _subprocess_call(command_list)


class GDALRasterToPNG(GDALProcessor):

    """ Raster to PNG processor """

    def __init__(self):
        GDALProcessor.__init__(self)
        self._process_type = 'topng'
        self._expect_format = 'PNG'

        # set parameters
        self._parameter_list = [
                                '-of', self._expect_format,
                                '-q',
                                ]

    def _do_process(self, source_file, target_file):
        command_list = ['gdal_translate', ]
        command_list.extend(self._parameter_list)
        command_list.extend([source_file, target_file])
        _subprocess_call(command_list)


class GDALFixMetaData(GDALProcessor):

    """ Set GEO meta data to raster

    fix_srs:
        EPSG code. eg, 4326.

    fix_envelope:
        a tuple. eg, (minx, miny, maxx, maxy).

    set_tiled:
        not implemented

    set_compressed:
        not implemented

    set_nodata:
        nodata value. eg, -32768.

    """

    def __init__(self, fix_srs=None,
                       fix_envelope=None,
                       set_tiled=False,
                       set_compressed=False,
                       set_nodata=None):
        GDALProcessor.__init__(self)
        self._process_type = 'metadata'

        # set parameters
        parameter_list = ['-q', ]
        if fix_srs:
            assert isinstance(fix_srs, int)
            parameter_list.extend(['-a_srs', 'EPSG:%d' % fix_srs])
        if fix_envelope:
            assert isinstance(fix_envelope, tuple) and len(fix_envelope) == 4
            minx, miny, maxx, maxy = map(str, fix_envelope)
            parameter_list.extend(['-a_ullr', minx, miny, maxx, maxy])
        if set_nodata:
            assert isinstance(set_nodata, int)
            parameter_list.extend(['-a_nodata', str(set_nodata)])

        if len(parameter_list) == 1:
            raise Exception('Insufficient parameters')

        self._parameter_list = parameter_list

    def _do_process(self, source_file, target_file):
        command_list = ['gdal_translate', ]
        command_list.extend(self._parameter_list)
        command_list.extend([source_file, target_file])
        _subprocess_call(command_list)


class GDALWarper(GDALProcessor):

    """ Warp raster from different spatial reference system """

    def __init__(self, dst_epsg, size=None, src_epsg=None):
        GDALProcessor.__init__(self)
        self._process_type = 'warp'
        assert isinstance(dst_epsg, int)

        # set parameters
        self._parameter_list = [
                                # warp parameters
                                '-t_srs', 'EPSG:%d' % dst_epsg,
                                # resample method
                                '-r', 'cubicspline',
                                # set work memory to 512M, the default is small
                                '-wm', '256M',
                                # quite mode
                                '-q',
                                ]
        if src_epsg:
            assert isinstance(src_epsg, int)
            self._parameter_list.extend(['-s_srs', 'EPSG:%d' % src_epsg])

        if size:
            assert isinstance(size, tuple)
            width, height = size
            assert isinstance(width, int)
            assert isinstance(height, int)
            self._parameter_list.extend(['-ts', str(width), str(height), ])

    def _do_process(self, source_file, target_file):
        command_list = ['gdalwarp', ]
        command_list.extend(self._parameter_list)
        command_list.extend([source_file, target_file])
        _subprocess_call(command_list)
