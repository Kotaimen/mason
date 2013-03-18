# -*- coding:utf-8 -*-
'''
Wrapper for GDAL tools

Created on Aug 30, 2012
@author: ray
'''
import re
import subprocess
from osgeo import osr

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


def gdal_hillshading(src, dst, zfactor, scale, altitude, azimuth):
    """
    @param zfactor: vertical exaggeration
    @param scale: ratio of vertical units to horizontal
        Feet:Latlong use scale=370400
        Meters:LatLong use scale=111120
    @param azimuth: azimuth of the light.
    @param altitude: altitude of the light, in degrees.
   """
    command_list = [
        'gdaldem', 'hillshade',
        src, dst,
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
    _subprocess_call(command_list)


def gdal_colorrelief(src, dst, color_context):
    """
    @param color_context: color description:
            3500   white
            2500   235:220:175
            50%    190 185 135
            700    240 250 150
            0      50  180  50
            nv     0   0   0
    """
    command_list = ['gdaldem', 'color-relief',
                    # input and output
                    src,
                    color_context,
                    dst,
                    # add an alpha channel
                    '-alpha',
                    # quite mode
                    '-q'
                    ]
    _subprocess_call(command_list)
