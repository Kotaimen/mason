"""
Crop given image data into smaller tiled images

Created on May 13, 2012

@author: Kotaimen
"""


import io
import subprocess

try:
    import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    output = subprocess.check_output(['convert', '-version'])
    # XXX: Check version? requires 6.5+.
    HAS_IMAGEMAGICK = True
except Exception:
    HAS_IMAGEMAGICK = False

if not (HAS_PIL or HAS_IMAGEMAGICK):
    raise ImportError('Requires ImageMagick or PIL but got nothing')


def gridcrop(image_data, rows, columns, ext):

    if HAS_PIL and ext in ['png', 'jpg']:
        return dict(gridcrop_pil(image_data, rows, columns, ext))
    else:
        return dict(gridcrop_magick(image_data, rows, columns, ext))


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


def gridcrop_pil(image_data, rows, columns, ext):

    if ext == 'jpg':
        ext = 'jpeg'
    elif ext == 'tif':
        ext = 'tiff'

    big_image = Image.open(_BytesIO(image_data))

    width, height = big_image.size
    assert width % rows == 0
    assert height % columns == 0

    grid_width = width // rows
    grid_height = height // rows

    for row in range(0, rows):
        for column in range(0, columns):
            left = row * grid_width
            top = column * grid_height
            right = left + grid_width
            bottom = top + grid_height

            crop_box = (left, top, right, bottom)

            grid_image = big_image.crop(crop_box)
            buf = _BytesIO()
            # XXX: Can't find way to "preserve input quality"
            grid_image.save(buf, ext, quality=95)
            yield (row, column), buf.getvalue()


MAGIC_HEADERS = {'png': b'\x89PNG\r\n\x1a\n',
                 'jpg': b'\xff\xd8',
                 'tif': b'II*\x00',
                 }


def gridcrop_magick(image_data, rows, columns, ext):

    """ For imagemagick command, see

    http://www.imagemagick.org/Usage/crop/#crop_equal

    Imagemagick 6.5+ is required, Q8 takes less memory but is less accurate
    """

    args = ['convert',
            '-quiet', '-limit', 'thread', '1',
            '%s:-' % ext,
            '-crop',
            '%dx%d@' % (rows, columns),
            '+repage',
            '+adjoin',
            '-',
            ]
    popen = subprocess.Popen(args, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    stdout, stderr = popen.communicate(image_data)
    retcode = popen.poll()

    if retcode != 0:
        raise subprocess.CalledProcessError(retcode, args, stderr)

    # Imagemagick simply join image datas together when asked to write to stdout,
    # Have to separate image data using magic headers here...
    magic = MAGIC_HEADERS[ext]

    bodies = stdout.split(magic)
    assert len(bodies) == rows * columns + 1

    for n, body in enumerate(bodies[1:]):
        column = n // rows
        row = n % columns
        data = b''.join([magic, body])

        yield (row, column), data


def boxcrop(image_data, ext, size, crop_box):
    if ext == 'jpg':
        ext = 'jpeg'

    if ext in ['jpeg', 'png']:
        return boxcrop_pil(image_data, ext, size, crop_box)
    else:
        return boxcrop_imagemagick(image_data, ext, size, crop_box)


def boxcrop_pil(image_data, ext, size, crop_box):
    assert ext in ['jpeg', 'png']

    big_image = Image.open(_BytesIO(image_data))

    width, height = size
    left, top, right, bottom = crop_box
    assert (left < width and left < right and left > 0)
    assert (top < height and top < bottom and top > 0)

    crop_image = big_image.crop(crop_box)
    buf = _BytesIO()
    crop_image.save(buf, ext, quality=95)
    return buf.getvalue()


def boxcrop_imagemagick(image_data, ext, size, crop_box):

    width, height = size
    left, top, right, bottom = crop_box
    assert (left < width and left < right and left > 0)
    assert (top < height and top < bottom and top > 0)

    width = right - left
    height = bottom - top

    args = ['convert',
            '-quiet', '-limit', 'thread', '1',
            '%s:-' % ext,
            '-crop',
            '%dx%d%+d%+d' % (width, height, left, top),
            '%s:-' % ext,
            ]
    popen = subprocess.Popen(args, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    stdout, stderr = popen.communicate(image_data)
    retcode = popen.poll()

    if retcode != 0:
        raise subprocess.CalledProcessError(retcode, args, stderr)

    return stdout
