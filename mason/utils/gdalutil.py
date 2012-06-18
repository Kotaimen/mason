'''
Created on May 1, 2012

@author: ray
'''
import os
import re
import tempfile
import subprocess

try:
    stdout = subprocess.Popen(['gdalwarp', '--version'],
                              stdout=subprocess.PIPE).communicate()[0]
except OSError:
    raise ImportError("Can't find gdalwarp, please install GDAL")
gdal_version = float(re.search(r'^GDAL (\d\.\d)\.\d', stdout).group(1))
if gdal_version < 1.8:
    raise ImportError('Requires gdal 1.8 or later')

try:
    stdout = subprocess.Popen(['gdaldem'],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE).communicate()[0]
except OSError:
    raise ImportError("Can't find dgaldem, please install GDAL")

try:
    stdout = subprocess.Popen(['gdaltransform', '--help'],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE).communicate()[0]
except OSError:
    raise ImportError("Can't find gdaltransform, please install GDAL")


#==============================================================================
# Simple Wrapper of GDAL utilities
#==============================================================================
def _subprocess_call(command_list):
    return subprocess.check_call(command_list) == 0


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


def _make_tempfile_pair():
    suffix = '_%d' % os.getpid()
    fd1, srcname = tempfile.mkstemp(suffix)
    fd2, dstname = tempfile.mkstemp(suffix)

    os.close(fd1)
    os.close(fd2)

    return srcname, dstname


def gdal_hillshade(data,
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

    try:
        src_name, dst_name = _make_tempfile_pair()
        with open(src_name, 'wb') as fp:
            fp.write(data)

        command_list = ['gdaldem', 'hillshade',
                        src_name,
                        dst_name,
                        '-z', z,
                        '-s', s,
                        '-az', az,
                        '-alt', alt,
                        '-compute_edges',
                        '-of', image_type,
                        '-q'
                        ]

        command_list.extend(control_params)

        ret = _subprocess_call(command_list)
        if not ret:
            raise Exception('Failed to convert to hill shade.')

        with open(dst_name, 'rb') as fp:
            data = fp.read()

        return data

    finally:
        os.remove(src_name)
        os.remove(dst_name)


def gdal_colorrelief(data,
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

    try:
        src_name, dst_name = _make_tempfile_pair()
        with open(src_name, 'wb') as fp:
            fp.write(data)

        command_list = ['gdaldem', 'color-relief',
                        src_name,
                        color_context,
                        dst_name,
                        '-of', image_type,
                        '-q']

        command_list.extend(control_params)
        ret = _subprocess_call(command_list)
        if not ret:
            raise Exception('Failed to convert to color relief.')

        with open(dst_name, 'rb') as fp:
            data = fp.read()

        return data

    finally:
        os.remove(src_name)
        os.remove(dst_name)


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


def gdal_warp(data,
              envelope=None,
              srs=None,
              size=None,
              ):
    """ Warp DEM data to specified envelope, srs and size

    envelope
        bounding box of format (xmin, ymin, xmax, ymax)

    srs
        tuple of source and target srs, for example ('EPSG:4326', 'EPSG:3857')

    size
        tuple of result size in pixel, for example (256, 256)

    At least one parameter of envelope, srs, and size should be provided.
    Make sure gdaltransform amd gdalwarp is available on your system.
    """
    assert any((envelope is not None, srs is not None, size is not None))

    nodata = '-32768'
    command_list = ['gdalwarp',
                    '-srcnodata', nodata,
                    '-dstnodata', nodata,
                    '-r', 'cubicspline',
                    '-q',
                    ]
    if srs:
        src_srs, dst_srs = srs
        assert src_srs != dst_srs
        command_list.extend(['-s_srs', src_srs,
                             '-t_srs', dst_srs, ])

    if size:
        width, height = str(size[0]), str(size[1])
        command_list.extend(['-ts', width, height, ])

    if envelope:
        xmin, ymin, xmax, ymax = envelope
        if srs:
            coords = list(((xmin, ymin), (xmax, ymax)))
            coords_reprojected = list(gdal_transform(src_srs, dst_srs, coords))

            xmin, ymin = coords_reprojected[0]
            xmax, ymax = coords_reprojected[1]

        command_list.extend(['-te',
                             str(xmin), str(ymin), str(xmax), str(ymax)])

    try:
        src_name, dst_name = _make_tempfile_pair()
        with open(src_name, 'wb') as fp:
            fp.write(data)

        command_list.extend([src_name, dst_name])

        ret = _subprocess_call(command_list)
        if not ret:
            raise Exception('Failed to warp.')

        with open(dst_name, 'rb') as fp:
            data = fp.read()

        return data

    finally:
        os.remove(src_name)
        os.remove(dst_name)
