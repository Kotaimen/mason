'''
Created on Apr 19, 2013

@author: Kotaimen
'''

import io
import numpy
import scipy
from PIL import Image
import scipy.misc
from numba import autojit

from .cartographer import Cartographer
from ..core.geo import GoogleMercatorProjection, Coordinate

@autojit
def mandel(x, y, max_iters):
    i = 0
    c = complex(x, y)
    z = 0.0j
    for i in xrange(max_iters):
        z = z * z + c
        if (z.real * z.real + z.imag * z.imag) >= 4:
            return int(255 - 1.0 * i / max_iters * 255)

    return 0

@autojit
def create_fractal(min_x, max_x, min_y, max_y, image, iters):
    height = image.shape[0]
    width = image.shape[1]

    pixel_size_x = (max_x - min_x) / width
    pixel_size_y = (max_y - min_y) / height
    for x in range(width):
        real = min_x + x * pixel_size_x
        for y in range(height):
            imag = min_y + y * pixel_size_y
            color = mandel(real, imag, iters)
            image[y, x] = color

    return image


class _BytesIO(io.BytesIO):
    def fileno(self):
        raise AttributeError


class Mandelbrot(Cartographer):

    def __init__(self, maxiter=100):
        self._maxiter = maxiter
        self._proj = GoogleMercatorProjection()
        Cartographer.__init__(self, 'PNG')


    def render(self, envelope=(-180, -85, 180, 85), size=(256, 256)):
        image = numpy.zeros((size[0] * 2, size[1] * 2), dtype=numpy.uint8)
        # Map (-180, -90, 180, 90) as (-2, -2, 2, 2)
        left, bottom, right, top = envelope
        left, bottom = self._proj.project(Coordinate(left, bottom))
        right, top = self._proj.project(Coordinate(right, top))

        create_fractal((left - 0.5) * 2 - 0.5, (right - 0.5) * 2 - 0.5,
                       (bottom - 0.5) * 2, (top - 0.5) * 2,
                       image, self._maxiter)
        image = scipy.misc.toimage(numpy.flipud(image))
        image = image.resize(size, Image.ANTIALIAS)
        buf = _BytesIO()
        image.save(buf, 'png', optimize=True)

        return buf
