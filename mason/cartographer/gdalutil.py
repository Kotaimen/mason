'''
Created on May 1, 2012

@author: ray
'''
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

try:
    stdout = subprocess.Popen(['gdaltransform', '--help'],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE).communicate()[0]
except OSError:
    raise RuntimeError("Can't find gdaltransform, please install GDAL")


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


def _make_control_params(image_type, image_parameters):
    control_params = list()

    image_type = image_type.lower()
    assert image_type in ('gtiff', 'png', 'jpeg')
    if image_parameters:
        assert isinstance(image_parameters, dict)
        if image_type == 'jpeg':
            quality = image_parameters.get('quality', None)
            if not isinstance(quality, int):
                raise Exception('Quality should be an integer.')
            if quality > 100 or quality < 10:
                raise Exception('Invalid JPEG quality.')
            control_params.extend(['-co', "quality=%d" % quality])
    return control_params


def gdal_hillshade(src,
                   dst,
                   zfactor=1,
                   scale=1,
                   azimuth=315,
                   altitude=45,
                   image_type='gtiff',
                   image_parameters=None
                   ):
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

    image_type
        output file format (GTIFF, PNG, JPEG)

    image_parameters
        output file format parameters

    -compute_edges
        before gdal 1.8 a rectangle with nodata value will be generated with
        output files. This can be fixed with computed_edges option in gdal 1.8
        and later.

    """

    z, s, az, alt = map(str, (zfactor, scale, azimuth, altitude))
    control_params = _make_control_params(image_type, image_parameters)

    command_list = ['gdaldem', 'hillshade', src, dst,
                    '-z', z,
                    '-s', s,
                    '-az', az,
                    '-alt', alt,
                    '-compute_edges',
                    '-of', image_type,
                    '-q'
                    ]

    command_list.extend(control_params)

    return _subprocess_call(command_list)


def gdal_colorrelief(src,
                     dst,
                     color_context,
                     image_type='gtiff',
                     image_parameters=None):
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

    image_type
        output file format (GTIFF, PNG, JPEG)

    image_parameters
        output file format parameters
    """
    control_params = _make_control_params(image_type, image_parameters)
    command_list = ['gdaldem', 'color-relief', src, color_context, dst,
                    '-of', image_type,
                    '-q']

    command_list.extend(control_params)
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


def gdal_transform(src_srs, dst_srs, coordinates):
    """ Reprojects a list of coordinates into any supported projection

    Return generator of coordinates

    src_srs
        source spatial reference system

    dst_srs
        result spatial reference system

    coordinates
        list of coordinates or one coordinate
    """

    if isinstance(coordinates, tuple):
        coordinates = [coordinates, ]

    coodinates_str = '\n'.join('%f %f' % coord for coord in coordinates)
    try:
        stdout = subprocess.Popen(['gdaltransform',
                                   '-s_srs', src_srs,
                                   '-t_srs', dst_srs,
                                   ],
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE
                                  ).communicate(coodinates_str)[0]

        for transformed_coords in stdout.splitlines():
            x, y, _ = transformed_coords.split()
            yield (float(x), float(y))

    except Exception as e:
        raise GDALProcessError(str(e))
