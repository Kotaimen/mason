"""
Crop given image data into smaller tiled images

Created on May 13, 2012

@author: Kotaimen
"""


import io
import subprocess

try:
    import Image
except ImportError:
    raise

try:
    output = subprocess.check_output(['convert', '-version'])
except Exception:
    raise ImportError('Requires ImageMagick')


def gridcrop(image_data, rows, columns, ext):
    if ext in ['png', 'jpg']:
        return dict(gridcrop_pil(image_data, rows, columns, ext))
    else:
        # PIL don't handle tiff very well, let imagemagick deal with it
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


MAGIC_HEADERS = {'png':b'\x89PNG\r\n\x1a\n',
                 'jpg':b'\xff\xd8',
                 'tif':b'II*\x00',
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



