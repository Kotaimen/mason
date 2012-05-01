'''
Created on May 1, 2012

@author: ray
'''
import os
import subprocess

def _check_executable(executable_name):
    for path in os.environ['PATH'].split(os.pathsep):
        executable_path = os.path.join(path, executable_name)
        if os.path.exists(executable_path):
            return True
    return False

def _check_gdal_tools():
    gdal_tools = ['gdalwarp', 'gdaldem']
    for tool in gdal_tools:
        if not _check_executable(tool):
            raise ImportError('%s is not available' % tool)

_check_gdal_tools()


#===============================================================================
# Errors 
#===============================================================================
class GDALProcessError(Exception):
    pass

#===============================================================================
# Simple Wrapper of GDAL utilities
#===============================================================================   
def _subprocess_call(command_list):
    try:
        return subprocess.check_call(command_list) == 0
    except subprocess.CalledProcessError as e:
        raise GDALProcessError(repr(e))


def gdal_hillshade(src, dst, zfactor=1, scale=1, azimuth=315, altitude=45):
    """
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
    color_context:
        text file with the following format:
            3500   white
            2500   235:220:175
            50%   190 185 135
            700    240 250 150
            0      50  180  50
            nv     0   0   0
        nv: no data value
         
    """
    command_list = ['gdaldem', 'color-relief', src, color_context, dst, '-q']
    return _subprocess_call(command_list)

