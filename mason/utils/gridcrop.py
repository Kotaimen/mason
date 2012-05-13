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


def gridcrop(image_data, rows, columns, ext):

    return dict(gridcrop_pil(image_data, rows, columns, ext))


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

            grid_image.save(buf, ext)
            yield (row, column), buf.getvalue()


# TODO: Implement ImageMagick engine, subprocess call is ugly but is easily 
#       portable between differen python versions.

#
#MAGIC_HEADERS = dict(png=b'd',
#                     jpg=b'b',
#                     ) 
#
#
#def gridcrop_magick(image_data, rows, columns, ext):
#    
#    args = ['convert',
#            '-quiet', '-limit', 'thread', '1',
#            '%s:-' % ext,
#            '-crop',
#            '%dx%d@' % (rows, columns),
#            '-']
#            ]
#    popen = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
#                     stderr=subprocess.PIPE)
#    stdout, stderr = subprocess.check_output(image_data)
#    retcode = popen.poll()
#
#    if retcode != 0:
#        raise subprocess.CalledProcessError(retcode, args, stderr)
#    
#    # Imagemagick just join image data together when asked to write to stdout,
#    # Have to sperate image data using magic here...
#    


