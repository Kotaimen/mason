# -*- coding:utf-8 -*-
'''
mason.cartographer.relief

Created on May 3, 2013
@author: ray
'''
import os
import math
import Image
import numpy
from scipy import ndimage
from osgeo import osr

from ..utils import SpatialTransformer
from ..core.gridcrop import _BytesIO
from ..composer import ImageMagickComposer
from .cartographer import Cartographer
from .raster import MemoryRaster, GeoReference
from .raster import hillshade, aspect_and_slope, alpha_blend


def find_data(dirpath, minx, miny, maxx, maxy):
    assert (minx < maxx) and (miny < maxy)

    left, right = int(math.floor(minx)), int(math.ceil(maxx))
    bottom, top = int(math.floor(miny)), int(math.ceil(maxy))

    for i in range(left, right + 1):
        for j in range(bottom, top + 1):
            sign_we = 'e' if i >= 0 else 'w'
            sign_ns = 'n' if j >= 0 else 's'

            filename = '%s%02d%s%03d.flt' % (sign_ns, abs(j), sign_we, abs(i))
            fullpath = os.path.join(dirpath, filename)
            if os.path.exists(fullpath):
                yield fullpath
            filename = '%s%02d%s%03d.tif' % (sign_ns, abs(j), sign_we, abs(i))
            fullpath = os.path.join(dirpath, filename)
            if os.path.exists(fullpath):
                yield fullpath

            sign_we = 'E' if i >= 0 else 'W'
            sign_ns = 'N' if j >= 0 else 'S'
            filename = '%s%02d%s%03d.tif' % (sign_ns, abs(j), sign_we, abs(i))
            fullpath = os.path.join(dirpath, filename)
            if os.path.exists(fullpath):
                yield fullpath
            filename = '%s%02d%s%03d.hgt' % (sign_ns, abs(j), sign_we, abs(i))
            fullpath = os.path.join(dirpath, filename)
            if os.path.exists(fullpath):
                yield fullpath


def array2img(array):
    buf = _BytesIO()
    # XXX: loses detail when convert to byte image... can we use float TIFF instead?
    array = (254 * array).astype(numpy.ubyte)
    image = Image.fromstring('L', (array.shape[1], array.shape[0]), array.tostring())
    image.save(buf, 'jpeg', quality=100, optimized=True)
    data = buf.getvalue()
    return data


class ShadeRelief(Cartographer):

    def __init__(self, dataset_path,
                 zfactor=1,
                 scale=111120,
                 azimuth=315,
                 altitude=45):
        Cartographer.__init__(self, 'jpg')

        srs = osr.SpatialReference()
        srs.ImportFromEPSG(3857)

        self._project = srs.ExportToWkt()
        self._transformer = SpatialTransformer(4326, 3857)
        self._dataset_path = dataset_path
        if not isinstance(dataset_path, list):
            self._dataset_path = list((dataset_path,))

        self._zfactor = zfactor
        self._scale = scale
        self._aziumth = azimuth
        self._altitude = altitude

        self._composer = ImageMagickComposer('jpg')

        self._composer.setup_command('''
          ( {{diffuse}} -fill grey50 -colorize 100% )
          ( {{diffuse}} ) -compose blend -define compose:args=30% -composite
          ( {{detail}} 
          -fill #0055ff -tint 60 
          -gamma 0.75  ) -compose blend -define compose:args=40% -composite
          ( {{specular}} -gamma 2 
          -fill #ffcba6 -tint 120 
          ) -compose blend -define compose:args=30% -composite
          -quality 100
        ''')

    def render(self, envelope=(-180, -90, 180, 90), size=(256, 256)):

        minx, miny, maxx, maxy = envelope
        t_minx, t_miny, __foo = self._transformer.forward(minx, miny)
        t_maxx, t_maxy, __foo = self._transformer.forward(maxx, maxy)

        # HACK: fix coordinates error around +/-180, otherwise,
        #       GDAL will project -181 to 19926188.852 (+179),
        #       which causes render artifacts
        mark180, __foo, __foo = self._transformer.forward(180, 0)
        if minx < -180:
            assert minx > -360
            t_minx = -mark180 - (mark180 - t_minx)
        if maxx > 180:
            assert maxx < 360
            t_maxx = mark180 + (mark180 + t_maxx)

        width, height = size
        resx = (t_maxx - t_minx) / (width)
        resy = (t_maxy - t_miny) / (height)
        geotransform = t_minx, resx, 0, t_maxy, 0, -resy

        georeference = GeoReference(self._project, geotransform, size)

        try:
            raster = MemoryRaster(georeference)
            elevation = raster.read()
            for dirpath in self._dataset_path:

                if os.path.isfile(dirpath):
                    filenames = [dirpath]
                else:
                    filenames = list(find_data(dirpath, minx, miny, maxx, maxy))
                if not filenames:
                    continue

                try:
                    temp_raster = MemoryRaster(georeference)
                    temp_raster.mosaic(filenames)

                    temp_elevation = temp_raster.read()
                    valid_mask = numpy.not_equal(temp_elevation,
                                                 MemoryRaster.NODATA_VALUE)

                    nodata_mask = numpy.zeros_like(elevation)
                    nodata_mask[numpy.equal(elevation, MemoryRaster.NODATA_VALUE)] = 1
                    nodata_mask = ndimage.binary_dilation(nodata_mask, iterations=16)

                    fillmask = numpy.logical_and(nodata_mask, valid_mask)
                    elevation[fillmask] = temp_elevation[fillmask]
                finally:
                    temp_raster.close()

                if numpy.all(numpy.not_equal(elevation, MemoryRaster.NODATA_VALUE)):
                    break
        finally:
            raster.close()

        zfactor = self._zfactor
        scale = self._scale

        aspect, slope = aspect_and_slope(elevation, resx, resy, zfactor, scale)
        diffuse = hillshade(aspect, slope, self._aziumth, 35)
        specular = hillshade(aspect, slope, self._aziumth, 85)

        zfactor = zfactor / 2.0
        aspect, slope = aspect_and_slope(elevation, resx, resy, zfactor, scale)
        detail = hillshade(aspect, slope, self._aziumth, 65)

        raster.close()

        images = {
            'diffuse': (array2img(diffuse), '.jpg'),
            'detail': (array2img(detail), '.jpg'),
            'specular': (array2img(specular), '.jpg'),
        }

        hillshading = self._composer.compose(images)

        return hillshading
