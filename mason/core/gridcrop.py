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
# Check what engine we have...
#===============================================================================

try:
    import Image
    if Image.VERSION != '1.1.7':
        raise ImportError('Excepted PIL 1.1.7')
except ImportError:
    HAS_PIL = False
else:
    HAS_PIL = True


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

try:
    check_imagemagick()
except Exception:
    HAS_IMAGEMAGICK = False
    raise
else:
    HAS_IMAGEMAGICK = True

if not (HAS_PIL or HAS_IMAGEMAGICK):
    raise ImportError('Requires ImageMagick or PIL but got nothing')

#===============================================================================
# PIL Engine, only handles PNG and JPEG files
#===============================================================================


class _BytesIO(io.BytesIO):
    # HACK: PIL expects file like object throw "AttributeError" when its
    #       not really a file.  This works for StringIO but not BytesIO:
    #
    #           >>> buf=StringIO.StringIO()
    #           >>> buf.fileno()
    #           Traceback (most recent call last):
    #           File "<stdin>", line 1, in <module>
    #           AttributeError: StringIO instance has no attribute 'fileno'
    #
    #           >>> buf=io.BytesIO()
    #           >>> buf.fileno()
    #           Traceback (most recent call last):
    #           File "<stdin>", line 1, in <module>
    #           io.UnsupportedOperation: fileno
    #
    #      So we restore the good-old behavior here, and hope someone patch
    #      this in the future... (strangely this only happens when you try
    #      save jpeg images to BytesIO)
    def fileno(self):
        raise AttributeError


def buffer_crop_pil(image_data, size, buffer, format):
    im = Image.open(_BytesIO(image_data))
    width, height = size, size
    crop_box = [buffer, buffer, size - buffer, size - buffer]
    left, top, right, bottom = crop_box
    assert (left < width and left < right and left > 0)
    assert (top < height and top < bottom and top > 0)
    rgn = im.crop(crop_box)
    buf = _BytesIO()
    if format == Format.JPG:
        rgn.save(buf, 'jpeg', quality=90, optimize=True)
    elif format == Format.PNG:
        rgn.save(buf, 'png', optimize=True)
    else:
        raise 'Unsupported format %r' % format
    return buf.getvalue()


def grid_crop_pil(image_data, stride, size, buffer, format):
    big_image = Image.open(_BytesIO(image_data))

    width, height = size, size
    rows, columns = stride, stride

    grid_width = grid_height = (size - buffer * 2) // stride

    cropped = dict()

    for row in range(0, rows):
        for column in range(0, columns):
            left = row * grid_width + buffer
            top = column * grid_height + buffer
            right = left + grid_width
            bottom = top + grid_height

            crop_box = (left, top, right, bottom)
            print crop_box
            grid_image = big_image.crop(crop_box)
            buf = _BytesIO()

            if format == Format.JPG:
                grid_image.save(buf, 'jpeg', quality=90, optimize=True)
            elif format == Format.PNG:
                grid_image.save(buf, 'png', optimize=True)
            else:
                raise 'Unsupported format %r' % format
            cropped[(row, column)] = buf.getvalue()
    return cropped

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


def buffer_crop_imagemagick(image_data, size, buffer, format):
    if buffer == 0:
        return image_data

    command = ['-shave', '%dx%d' % (buffer, buffer), ]

    return convert(image_data, command, format)


def grid_crop_imagemagick(image_data, stride, size, buffer, format):

    width = height = size
    left, top, right, bottom = buffer, buffer, width - buffer, height - buffer

    command = [
            '-shave', '%dx%d' % (buffer, buffer),
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
# Select a engine
#===============================================================================

def buffer_crop(image_data, size, buffer, format):
    if False:  # HAS_PIL and format in [Format.JPG, Format.PNG]:
        return buffer_crop_pil(image_data, size, buffer, format)
    else:
        return buffer_crop_imagemagick(image_data, size, buffer, format)


def grid_crop(image_data, stride, size, buffer, format):
    if False:  # HAS_PIL and format in [Format.JPG, Format.PNG]:
        return grid_crop_pil(image_data, stride, size, buffer, format)
    else:
        return grid_crop_imagemagick(image_data, stride, size, buffer, format)


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

