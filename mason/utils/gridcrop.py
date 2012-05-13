"""
Crop given image data into smaller tiled images

Created on May 13, 2012

@author: Kotaimen
"""


import io
import Image
import subprocess


def gridcrop(data, rows, columns, ext):
    # XXX: dummy impl
    for row in range(rows):
        for column in range(columns):
            yield (row, column), b''


def gridcrop_pil(image_data, rows, columns, ext):

    big_image = Image.open(io.BytesIO(image_data))

    width, height = big_image.size
    assert width % rows == 0
    assert height % columns == 0

    grid_width = width // rows
    grid_height = height // height

    for row in range(0, rows):
        for column in range(0, columns):
            left = row * grid_width
            top = column * grid_height
            right = left + grid_width
            bottom = top + grid_height

            crop_box = (left, top, right, bottom)

            grid_image = big_image.crop(crop_box)
            buf = io.BytesIO()

            grid_image.save(buf, ext)
            yield (row, column), buffer.getvalue()

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


