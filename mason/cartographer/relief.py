# -*- coding:utf-8 -*-
'''
mason.cartographer.raster

Created on Apr 10, 2013
@author: ray
'''
import io
import re
import os
import math

from PIL import Image
import numpy
import scipy

from scipy import ndimage
from osgeo import gdal, gdalconst, osr

from ..utils import TempFile, Timer
from ..core.gridcrop import _BytesIO
from ..composer import ImageMagickComposer
from .cartographer import Cartographer


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


class GeoRaster(object):

    def __init__(self, srid, geotransform, size, bands=1):

        m = re.match('EPSG:(?P<epsg_id>\d+)', srid, re.IGNORECASE)
        if not m:
            raise Exception('Unknown srid %s. Only support EPSG now.' % srid)

        epsg_id = int(m.group('epsg_id'))
        self._srs = osr.SpatialReference()
        self._srs.ImportFromEPSG(epsg_id)
        self._projection = self._srs.ExportToWkt()

        self._width = size[0]
        self._height = size[1]

        minx, resx, skewx, maxy, skewy, resy = geotransform
        self._resx = resx
        self._resy = -resy
        maxx = minx + self._resx * self._width
        miny = maxy - self._resy * self._height
        self._envelope = (minx, miny, maxx, maxy)

        self._bands = bands

        driver = gdal.GetDriverByName('MEM')

        ds = driver.Create('',
                           self._width,
                           self._height,
                           self._bands,
                           gdal.GDT_Float32)
        ds.SetGeoTransform(geotransform)
        ds.SetProjection(self._projection)

        ds.GetRasterBand(1).WriteArray(numpy.ones(size, numpy.float32) * -32768, 0, 0)
        ds.GetRasterBand(1).SetNoDataValue(-32768)
        ds.GetRasterBand(1).SetColorInterpretation(gdalconst.GCI_Undefined)

        self._raster = ds

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def resx(self):
        return self._resx

    @property
    def resy(self):
        return self._resy

    @property
    def envelope(self):
        return self._envelope

    @property
    def projection(self):
        return self._projection

    @property
    def bands(self):
        return self._bands

    def read(self, band=1, offx=0, offy=0, winx=None, winy=None):
        data = self._raster.GetRasterBand(1).ReadAsArray()
        nodata = self._raster.GetRasterBand(1).GetNoDataValue()
        data = numpy.ma.masked_values(data, nodata)
        return data

    def write(self, data, offx=0, offy=0):
        self._raster.GetRasterBand(1).WriteArray(data, offx, offy)

    def mosaic(self, filename):
        source = gdal.Open(filename, gdalconst.GA_ReadOnly)
        if not source:
            raise Exception('Source file %s not found' % filename)
        source_proj = source.GetProjection()

        target = self._raster
        target_proj = target.GetProjection()

        # figure out resample method
        source_geotransform = source.GetGeoTransform()
        source_resx = source_geotransform[1]
        source_resy = -source_geotransform[5]

        source_minx = source_geotransform[0]
        source_maxy = source_geotransform[3]
        source_miny = source_maxy - source_resy * source.RasterYSize
        source_maxx = source_minx + source_resx * source.RasterXSize

        fr_srs = osr.SpatialReference()
        fr_srs.ImportFromWkt(source_proj)
        to_srs = osr.SpatialReference()
        to_srs.ImportFromWkt(target_proj)
        transformer = osr.CoordinateTransformation(fr_srs, to_srs)
        source_minx, source_miny, __foo = transformer.TransformPoint(source_minx, source_miny)
        source_maxx, source_maxy, __foo = transformer.TransformPoint(source_maxx, source_maxy)

        target_geotransform = target.GetGeoTransform()
        target_resx = target_geotransform[1]
        target_resy = -target_geotransform[5]

        # resy < 0
        org_width = source.RasterXSize
        org_height = source.RasterYSize
        proj_width = (source_maxx - source_minx) / target_resx
        proj_height = (source_maxy - source_miny) / target_resy

        zoom_ratio = min(proj_width / org_width, proj_height / org_height)
        resample = None
        if zoom_ratio < 0.5:
            resample = gdalconst.GRA_Cubic
        elif zoom_ratio > 1.2:
            resample = gdalconst.GRA_CubicSpline
        else:
            resample = gdalconst.GRA_Bilinear

        ret = gdal.ReprojectImage(source,
                                  target,
                                  source_proj,
                                  target_proj,
                                  resample,
                                  )
        # close source data
        source = None
        return gdalconst.CE_Failure != ret

    def blend(self, georaster, proportion):
        assert proportion <= 1.0 and proportion >= 0
        assert georaster.projection == georaster.projection

        data = self.read()
        blend_data = georaster.read()

        assert data.shape == blend_data.shape

        # alpha composite
        data = data * (1 - proportion) + blend_data * proportion

        self.write(data, 0, 0)
        return True

    def fillnodata(self):
        band = self._raster.GetRasterBand(1)
        ret = gdal.FillNodata(band, None, 500, 0)
        return gdalconst.CE_Failure != ret

    def aspect_and_slope(self, zfactor, scale):

        elevation = self.read()

        kernel = [[1, 0, -1], [2, 0, -2], [1, 0, -1]]
        dx = ndimage.convolve(elevation,
                numpy.array(kernel) / (8. * self._resx * scale),
                mode='nearest')

        kernel = [[1, 2, 1], [0, 0, 0], [-1, -2, -1]]
        dy = ndimage.convolve(elevation,
                numpy.array(kernel) / (8. * self._resy * scale),
                mode='nearest')

        slope = numpy.arctan(zfactor * numpy.hypot(dx, dy))
        aspect = math.pi / 2 - numpy.arctan2(dy, -dx)

        return aspect, slope

    def hillshade(self, aspect, slope, azimuth, altitude):
        zenith = math.radians(90. - altitude % 360.)
        azimuth = math.radians(azimuth)
        hillshade = 1 * ((math.cos(zenith) * numpy.cos(slope)) +
           (math.sin(zenith) * numpy.sin(slope) * numpy.cos(azimuth - aspect)))

        hillshade[hillshade < 0] = 1 / 255
        return hillshade

    def summary(self):
        print '*' * 80
        print 'size: %dx%dx%d' % (self.width, self.height, self.bands)
        print 'resolution: %f x %f' % (self.resx, self.resy)
        print 'envelope: (%f, %f, %f, %f)' % self.envelope
        print 'projection: %s' % self.projection
        print '*' * 80

    def close(self):
        self._raster = None

    @staticmethod
    def from_file(filename):
        source = gdal.Open(filename, gdalconst.GA_ReadOnly)
        if not source:
            raise Exception('Source file %s not found' % filename)

        geotransform = source.GetGeoTransform()
        projection = source.GetProjection()

        srs = osr.SpatialReference()
        srs.ImportFromWkt(projection)

        epsg_id = int(srs.AutoIdentifyEPSG())
        if not epsg_id:
            if srs.IsGeographic():
                epsg_id = int(srs.GetAuthorityCode('GEOGCS'))
            else:
                epsg_id = int(srs.GetAuthorityCode('PROJCS'))
        srid = 'EPSG:%d' % epsg_id

        size = (source.RasterXSize, source.RasterYSize)

        raster = GeoRaster(srid, geotransform, size, bands=1)
        raster.write(source.GetRasterBand(1).ReadAsArray(), 0, 0)

        return raster


class ShadeRelief(Cartographer):

    def __init__(self, dataset_path,
                 zfactor=1,
                 scale=111120,
                 azimuth=315,
                 altitude=45):
        Cartographer.__init__(self, 'jpg')

        fr_srs = osr.SpatialReference()
        fr_srs.ImportFromEPSG(4326)
        to_srs = osr.SpatialReference()
        to_srs.ImportFromEPSG(3857)

        self._transformer = osr.CoordinateTransformation(fr_srs, to_srs)
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
          ( {{detail}} -fill #0055ff -tint 60 -gamma 0.75  ) -compose blend -define compose:args=40% -composite
          ( {{specular}} -gamma 2 -fill #ffcba6 -tint 120 ) -compose blend -define compose:args=30% -composite
          -quality 100
        ''')


    def array2img(self, array):
        buf = _BytesIO()
        # XXX: loses detail when convert to byte image... can we use float TIFF instead?
        array = (254 * array).astype(numpy.ubyte)
        image = scipy.misc.toimage(array)
        image.save(buf, 'jpeg', quality=100, optimized=True)
        data = buf.getvalue()
        return data

    def render(self, envelope=(-180, -90, 180, 90), size=(256, 256)):

        minx, miny, maxx, maxy = envelope
        t_minx, t_miny, __foo = self._transformer.TransformPoint(minx, miny)
        t_maxx, t_maxy, __foo = self._transformer.TransformPoint(maxx, maxy)

        # HACK: fix coordinates error around +/-180, otherwise, GDAL will project
        #       -181 to 19926188.852, which causes render artifacts
        mark180, __foo, __foo = self._transformer.TransformPoint(180, 0)
        if minx < -180:
            assert minx > -360
            t_minx = -mark180 - (mark180 - t_minx)
        if maxx > 180:
            assert maxx < 360
            t_maxx = mark180 + (mark180 + t_maxx)

        width, height = size
        resx = (t_maxx - t_minx) / (width)
        resy = (t_maxy - t_miny) / (height)

        # minx, resx, skewx, maxy, skewy, resy
        geotransform = t_minx, resx, 0, t_maxy, 0, -resy

        raster = GeoRaster('EPSG:3857', geotransform, size)

        for dirpath in self._dataset_path:
#            print 'mosaic....'
            if os.path.isfile(dirpath):
                raster.mosaic(dirpath)
            else:
                for filename in find_data(dirpath, minx, miny, maxx, maxy):
    #                print filename
                    raster.mosaic(filename)
#            raster.fillnodata()
        raster.fillnodata()

        aspect, slope = raster.aspect_and_slope(self._zfactor, self._scale)
        diffuse = raster.hillshade(aspect, slope, self._aziumth, 35)
        specular = raster.hillshade(aspect, slope, self._aziumth, 85)

        aspect, slope = raster.aspect_and_slope(self._zfactor / 2.0, self._scale)
        detail = raster.hillshade(aspect, slope, self._aziumth, 65)

        raster.close()

        images = {
            'diffuse' : (self.array2img(diffuse), '.jpg'),
            'detail' : (self.array2img(detail), '.jpg'),
            'specular' : (self.array2img(specular), '.jpg'),
        }

        hillshading = self._composer.compose(images)


        return hillshading
