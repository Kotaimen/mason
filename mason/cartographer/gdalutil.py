'''
Created on May 1, 2012

@author: ray
'''
import os
import re
import subprocess

try:
    stdout = subprocess.Popen(['gdalwarp', '--version'],
                              stdout=subprocess.PIPE).communicate()[0]
except OSError:
    raise RuntimeError("Can't find gdalwarp, please install GDAL")
gdal_version = float(re.search(r'^GDAL (\d\.\d)\.\d', stdout).group(1))
if gdal_version < 1.9:
    raise RuntimeError('Requires gdal 1.9 or later')

try:
    stdout = subprocess.Popen(['gdaldem'],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE).communicate()[0]
except OSError:
    raise RuntimeError("Can't find dgaldem, please install GDAL")

#==============================================================================
# Errors
#==============================================================================

class GDALProcessError(Exception):
    pass


#==============================================================================
# Simple Wrapper of GDAL utilities
#==============================================================================
def _subprocess_call(command_list):
    try:
        return subprocess.check_call(command_list) == 0
    except subprocess.CalledProcessError as e:
        raise GDALProcessError(str(e))


def gdal_hillshade(src, dst, zfactor=1, scale=1, azimuth=315, altitude=45):
    """
    To generate a hill shade from dem data source.

    src, dst
        file path

    zfactor
        vertical exaggeration used to pre-multiply the elevations

    scale
        ratio of vertical units to horizontal.
        Feet:Latlong use scale=370400
        Meters:LatLong use scale=111120

    azimuth
        azimuth of the light.

    altitude
        altitude of the light, in degrees.

    -compute_edges
        before gdal 1.8 a rectangle with nodata value will be generated with
        output files. This can be fixed with computed_edges option in gdal 1.8
        and later.

    """
    z, s, az, alt = map(str, (zfactor, scale, azimuth, altitude))
    command_list = ['gdaldem', 'hillshade', src, dst,
                    '-z', z,
                    '-s', s,
                    '-az', az,
                    '-alt', alt,
                    '-compute_edges',
                    '-q'
                    ]
    return _subprocess_call(command_list)


def gdal_colorrelief(src, dst, color_context):
    """
    To generate a color relief from dem data source

    src, dst
        file path

    color_context
        text file with the following format:
            3500   white
            2500   235:220:175
            50%    190 185 135
            700    240 250 150
            0      50  180  50
            nv     0   0   0
        nv: no data value

    """
    command_list = ['gdaldem', 'color-relief', src, color_context, dst, '-q']
    return _subprocess_call(command_list)


def gdal_warp(src, dst, width, height):
    """
    To warp the dem data to specified width and height in pixel

    width
        image width in pixel

    height
        image height in pixel

    """
    nodata = '-32768'
    width, height = str(width), str(height)
    command_list = ['gdalwarp', '-ts', width, height,
                    '-srcnodata', nodata,
                    '-dstnodata', nodata,
                    '-r', 'cubicspline',
                    '-q',
                    src, dst]
    return _subprocess_call(command_list)
