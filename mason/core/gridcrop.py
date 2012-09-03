"""
Crop Metatile into smaller Tiles

Requires imagemagick 6.5+, Q16 for TIFF 16 images.

Created on May 13, 2012
@author: Kotaimen
"""

import io
import subprocess

from .format import Format
from .tile import Tile, MetaTile
#===============================================================================
# Imagemagick version check
#===============================================================================


def check_imagemagick():
    # Check image magick version
    try:
        output = subprocess.check_output(['convert', '-version'])
    except Exception as e:
        raise ImportError('Requires imagemagick to crop images (convert).\n%r' % e)
    import re
    match = re.search(r'Version: ImageMagick (\d+\.\d+)\.(\d+)-(\d+)', output)
    if not match:
        raise ImportError("Don't understand 'convert -version' output ")

    version = float(match.group(1)) + float(match.group(2)) * 0.01
    if version < 6.5:
        # Not sure lowest supported version, ubuntu 12.04 comes with 6.6.9
        raise ImportError('Requires ImageMagick 6.6.9 or higher')


# XXX: Check at first usage... 
check_imagemagick()


#===============================================================================
# ImageMagick commands
#===============================================================================


# Magic bytes for separating image byte streams
MAGIC_NUMBER = dict(PNG=b'\x89PNG\r\n\x1a\n',
                    JPG=b'\xff\xd8',
                    TIFF=b'II*\x00',)


def convert(input_data, command, input_format, output_format=None):

    """ Call 'convert' with one input image from stdin and one output image as
    stdout """

    input_extension = input_format.extension[1:]
    if output_format is None:
        output_extension = input_extension
    else:
        output_extension = output_format.extension[1:]

    args = ['convert',
            '-quiet', '-limit', 'thread', '1',
            '%s:-' % input_extension, ]

    if input_format == output_format == Format.JPG:
        # Preserve JPG quality settings
        command.extend(['-define', 'jpeg:preserve-settings', ])

    args.extend(command)
    args.extend(['%s:-' % output_extension, ])

    popen = subprocess.Popen(args, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    output_data, stderr = popen.communicate(input_data)
    retcode = popen.poll()

    if retcode != 0:
        raise subprocess.CalledProcessError(retcode, args, stderr)

    return output_data


def buffer_crop(image_data, size, buffer, format):

    width = height = size
    left, top, right, bottom = buffer, buffer, width - buffer, height - buffer
    assert (left < width and left < right and left > 0)
    assert (top < height and top < bottom and top > 0)

    width = right - left
    height = bottom - top

    command = ['-crop', '%dx%d%+d%+d' % (width, height, left, top), ]

    return convert(image_data, command, format)


def grid_crop(image_data, stride, size, buffer, format):

    width = height = size
    left, top, right, bottom = buffer, buffer, width - buffer, height - buffer

    command = [
            '-crop', '%dx%d%+d%+d' % (width, height, left, top),
            '-crop', '%dx%d@' % (stride, stride),
            '+repage', '+adjoin',
            ]

    image_stream = convert(image_data, command, format)

    # Imagemagick simply join several image datas together when asked to
    # write to stdout... have to separate images using magic number here
    magic = MAGIC_NUMBER[format.name]

    bodies = image_stream.split(magic)
    assert len(bodies) == stride * stride + 1

    cropped = dict()

    for n, body in enumerate(bodies[1:]):
        column = n // stride
        row = n % stride
        # split() throws separator away so add it back here
        data = b''.join([magic, body])

        cropped[(row, column)] = data

    return cropped


#===============================================================================
# Cropper
#===============================================================================

def metatile_fission(metatile):

    format = metatile.format
    # Only supports clip/crop JPG/PNG, since crop GeoTIFF/TIFF may  
    # lose color depth and geo reference information
    assert format in [Format.PNG, Format.JPG, Format.TIFF]
    stride = metatile.index.stride
    size = metatile.index.tile_size
    buffer = metatile.index.buffer

    tile_indexes = metatile.index.fission()

    cropped = grid_crop(metatile.data, stride, size, buffer, format)
    tiles = list()

    for tile_index in tile_indexes:
        x = tile_index.x - metatile.index.x
        y = tile_index.y - metatile.index.y
        data = cropped[(x, y)]
        tile = Tile.from_tile_index(tile_index,
                                    data,
                                    fmt=format,
                                    mtime=metatile.mtime)
        tiles.append(tile)

    return tiles

