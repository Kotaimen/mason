# -*- coding:utf-8 -*-
'''
mason.cartographer.raster

Created on May 2, 2013
@author: ray
'''
import os
import io
import math
import numpy
from xml.etree import ElementTree
from scipy import ndimage, misc
from osgeo import gdal, gdalconst, osr

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


class GeoReference(object):

    def __init__(self, project, geotransform, size):
        self._project = project
        self._geotransform = geotransform
        self._size = size

        minx, resx, skewx, maxy, skewy, resy = geotransform
        resy = -resy  # y resolution < 0
        width, height = size

        maxx = minx + width * resx
        miny = maxy - height * resy

        self._resx = resx
        self._resy = resy
        self._envelope = minx, miny, maxx, maxy

    @property
    def project(self):
        return self._project

    @property
    def size(self):
        return self._size

    @property
    def geotransform(self):
        return self._geotransform

    @property
    def envelope(self):
        return self._envelope

    @property
    def resx(self):
        return self._resx

    @property
    def resy(self):
        return self._resy


def alpha_blend(elevation1, elevation2, proportion=0.5):
    elevation = elevation1 * (1 - proportion) + elevation2 * proportion
    return elevation


def aspect_and_slope(elevation, resx, resy, zfactor, scale):
    """ create aspect and slope from raster """
    kernel = numpy.array([[1, 0, -1], [2, 0, -2], [1, 0, -1]])
    dx = ndimage.convolve(elevation, kernel / (8. * resx), mode='nearest')

    kernel = numpy.array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]])
    dy = ndimage.convolve(elevation, kernel / (8. * resy), mode='nearest')

    slope = numpy.arctan(zfactor / scale * numpy.hypot(dx, dy))
    aspect = math.pi / 2 - numpy.arctan2(dy, -dx)

    return aspect, slope


def hillshade(aspect, slope, azimuth, altitude):
    """ create hillshade from aspect and slope """
    zenith = math.radians(90. - altitude % 360.)
    azimuth = math.radians(azimuth)

    hillshade = 1 * ((math.cos(zenith) * numpy.cos(slope)) +
       (math.sin(zenith) * numpy.sin(slope) * numpy.cos(azimuth - aspect)))

    hillshade[hillshade < 0] = 1 / 254
    return hillshade


def array2img(array):
    pass


def _intersection(src_envelop, dst_envelope):
    ''' return box of overlap area relative to dst_envelope '''
    s_minx, s_miny, s_maxx, s_maxy = src_envelop
    t_minx, t_miny, t_maxx, t_maxy = dst_envelope

    minx = max(s_minx, t_minx)
    maxx = min(s_maxx, t_maxx)
    if maxx <= minx:
        return None

    miny = max(s_miny, t_miny)
    maxy = min(s_maxy, t_maxy)
    if maxy <= miny:
        return None

    return (minx, miny, maxx, maxy)


#==============================================================================
# Rasters
#==============================================================================
class Raster(object):

    """ Base Class of Raster Object """

    @property
    def georeference(self):
        raise NotImplementedError

    def read(self, offx=0, offy=0, winx=None, winy=None):
        raise NotImplementedError

    def write(self, data, offx=0, offy=0):
        raise NotImplementedError

    def mosaic(self, filename):
        raise NotImplementedError

    def fillnodata(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError


class FileRaster(Raster):

    """ Read Only file raster """

    def __init__(self, filename):

        raster = gdal.OpenShared(filename, gdalconst.GA_ReadOnly)
        if not raster:
            raise Exception('Source file %s not found' % filename)

        projection = raster.GetProjection()
        geotransform = raster.GetGeoTransform()
        size = (raster.RasterXSize, raster.RasterYSize)

        self._georeference = GeoReference(projection, geotransform, size)
        self._raster = raster

    @property
    def georeference(self):
        return self._georeference

    def read(self, offx=0, offy=0, winx=None, winy=None):
        band = self._raster.GetRasterBand(1)
        data = band.ReadAsArray(offx, offy, winx, winy)
        return data

    def close(self):
        self._raster = None


class MemoryRaster(Raster):

    """ GDAL In-Memory Raster Wrapper """

    NODATA_VALUE = -32768

    def __init__(self, georeference):
        self._georeference = georeference

        width, height = georeference.size
        driver = gdal.GetDriverByName('MEM')
        raster = driver.Create('', width, height, 1, gdalconst.GDT_Float64)
        raster.SetGeoTransform(georeference.geotransform)
        raster.SetProjection(georeference.project)

        band = raster.GetRasterBand(1)
        band.SetNoDataValue(self.NODATA_VALUE)
        band.SetColorInterpretation(gdalconst.GCI_Undefined)
        band.Fill(self.NODATA_VALUE)
        self._raster = raster

    @property
    def georeference(self):
        return self._georeference

    def read(self, offx=0, offy=0, winx=None, winy=None):
        band = self._raster.GetRasterBand(1)
        data = band.ReadAsArray(offx, offy, winx, winy)
        return data

    def write(self, data, offx=0, offy=0):
        band = self._raster.GetRasterBand(1)
        band.WriteArray(data, offx, offy)

    def mosaic(self, filenames):

        vrt = VirtualRaster.from_filenames(filenames)
        if not vrt:
            return None



    def fillnodata(self):
        band = self._raster.GetRasterBand(1)
        gdal.FillNodata(band, None, 500, 0)

    def close(self):
        self._raster = None


class VirtualRaster(Raster):

    def __init__(self, georeference):
        self._georeference = georeference

        width, height = georeference.size
        driver = gdal.GetDriverByName('VRT')
        vrt = driver.Create('', width, height, 1, gdalconst.GDT_Float64)
        vrt.SetGeoTransform(georeference.geotransform)
        vrt.SetProjection(georeference.project)

        band = vrt.GetRasterBand(1)
        band.SetNoDataValue(-32768)

        self._raster = vrt

    def mosaic(self, filename):

        source = FileRaster(filename)
        src_ref = source.georeference
        dst_ref = self._georeference

        if src_ref.project != dst_ref.project:
            raise RuntimeError('projection of source files is inconsistent.')

        overlap = _intersection(src_ref.envelope, dst_ref.envelope)
        if not overlap:
            return None

        # create vrt xml element
        complex_source = ElementTree.Element('ComplexSource')
        source_file = ElementTree.Element('SourceFilename', relativeToVRT='1')
        source_file.text = filename
        source_band = ElementTree.Element('SourceBand')
        source_band.text = '1'
        band = source.GetRasterBand(1)
        blocksize = band.GetBlockSize()
        source_prop = ElementTree.Element('SourceProperties',
            RasterXSize=str(source.RasterXSize),
            RasterYSize=str(source.RasterYSize),
            DataType=gdal.GetDataTypeName(band.DataType),
            BlockXSize=str(blocksize[0]),
            BlockYSize=str(blocksize[1]),
            )

        source_nodata = ElementTree.Element('NODATA')
        source_nodata.text = str(band.GetNoDataValue())

        left, bottom, right, top = overlap
        src_minx, src_miny, src_maxx, src_maxy = src_ref.envelope
        dst_minx, dst_miny, dst_maxx, dst_maxy = dst_ref.envelope

        s_offx = (left - src_minx) / src_ref.resx + 0.5
        s_offy = (src_maxy - top) / src_ref.resy + 0.5
        s_sizex = (right - left) / src_ref.resx + 0.5
        s_sizey = (top - bottom) / src_ref.resy + 0.5

        t_offx = (left - dst_minx) / dst_ref.resx + 0.5
        t_offy = (dst_maxy - top) / dst_ref.resy + 0.5
        t_sizex = (right - left) / dst_ref.resx + 0.5
        t_sizey = (top - bottom) / dst_ref.resy + 0.5

        src_rect = ElementTree.Element('SrcRect',
            xOff=str(int(s_offx)),
            yOff=str(int(s_offy)),
            xSize=str(int(s_sizex)),
            ySize=str(int(s_sizey)),
            )
        dst_rect = ElementTree.Element('DstRect',
            xOff=str(int(t_offx)),
            yOff=str(int(t_offy)),
            xSize=str(int(t_sizex)),
            ySize=str(int(t_sizey)),
            )

        complex_source.append(source_file)
        complex_source.append(source_band)
        complex_source.append(source_prop)
        complex_source.append(src_rect)
        complex_source.append(dst_rect)

        tree = ElementTree.ElementTree(complex_source)
        buff = io.BytesIO()
        tree.write(buff)
        xml = str(buff.getvalue())

        band = self._raster.GetRasterBand(1)
        metadata = band.GetMetadata()
        metadata['source_%d' % len(metadata)] = xml
        band.SetMetadata(metadata, 'vrt_sources')

        source.close()

    def reproject(self, projection, geotransform, size):

        width, height = size
        dst_ref = GeoReference(projection, geotransform, size)

        driver = gdal.GetDriverByName('MEM')
        ds = driver.Create('', width, height, 1, gdal.GDT_Float32)
        ds.SetGeoTransform(geotransform)
        ds.SetProjection(projection)
        ds.GetRasterBand(1).SetNoDataValue(-32768)
        ds.GetRasterBand(1).SetColorInterpretation(gdalconst.GCI_Undefined)

        # figure out resample method
        vrt_ref = self._georeference
        vrt_minx, vrt_miny, vrt_maxx, vrt_maxy = vrt_ref.envelope

        dst_srs = osr.SpatialReference()
        dst_srs.ImportFromWkt(dst_ref.project)
        vrt_srs = osr.SpatialReference()
        vrt_srs.ImportFromWkt(vrt_ref.project)
        transformer = osr.CoordinateTransformation(vrt_srs, dst_srs)
        dst_minx, dst_miny, _z = transformer.TransformPoint(vrt_minx, vrt_miny)
        dst_maxx, dst_maxy, _z = transformer.TransformPoint(vrt_maxx, vrt_maxy)

        # resy < 0
        org_width, org_height = vrt_ref.size
        proj_width = (dst_maxx - dst_minx) / dst_ref.resx
        proj_height = (dst_maxy - dst_miny) / dst_ref.resy

        zoom_ratio = min(proj_width / org_width, proj_height / org_height)
        resample = None
        if zoom_ratio < 0.5:
            resample = gdalconst.GRA_Cubic
        elif zoom_ratio > 1.2:
            resample = gdalconst.GRA_CubicSpline
        else:
            resample = gdalconst.GRA_Bilinear

        gdal.ReprojectImage(self._raster,
                            ds,
                            vrt_ref.project,
                            dst_ref.project,
                            resample,
                            )

        data = ds.ReadAsArray()
        ds = None
        return data

    def close(self):
        self._raster = None

    @staticmethod
    def from_filenames(filenames):
        if not filenames:
            raise RuntimeError('Empty file list')

        sample = FileRaster(filenames[0])
        sample_ref = sample.georeference()

        proj = sample_ref.project
        minx, miny, maxx, maxy = sample_ref.envelope
        resx, resy = sample_ref.resx, sample_ref.resy

        for filename in filenames[1:]:
            source = FileRaster(filename)
            src_ref = source.georeference

            src_proj = src_ref.project
            src_minx, src_miny, src_maxx, src_maxy = src_ref.envelope
            src_resx, src_resy = src_ref.resx, src_ref.resy

            if src_proj != proj:
                raise RuntimeError('projection is inconsistent.')

            minx = min(minx, src_minx)
            miny = min(miny, src_miny)
            maxx = max(maxx, src_maxx)
            maxy = max(maxy, src_maxy)

            resx = min(resx, src_resx)
            resy = min(resy, src_resy)

        size = int((maxx - minx) / resx + 0.5), int((maxy - miny) / resy + 0.5)
        geotransform = minx, resx, 0, maxy, 0, -resy

        ref = GeoReference(proj, geotransform, size)
        vrt = VirtualRaster(ref)
        for filename in filenames:
            vrt.mosaic(filename)

        return vrt


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
        image = misc.toimage(array)
        image.save(buf, 'jpeg', quality=100, optimized=True)
        data = buf.getvalue()
        return data

    def render(self, envelope=(-180, -90, 180, 90), size=(256, 256)):

        minx, miny, maxx, maxy = envelope
        t_minx, t_miny, __foo = self._transformer.TransformPoint(minx, miny)
        t_maxx, t_maxy, __foo = self._transformer.TransformPoint(maxx, maxy)

        width, height = size
        resx = (t_maxx - t_minx) / (width)
        resy = (t_maxy - t_miny) / (height)

        # minx, resx, skewx, maxy, skewy, resy
        geotransform = t_minx, resx, 0, t_maxy, 0, -resy

        dst_srs = osr.SpatialReference()
        dst_srs.ImportFromEPSG(3857)
        proj = dst_srs.ExportToWkt()

        georeference = GeoReference(proj, geotransform, size)
        raster = MemoryRaster(georeference)

        elevation = raster.read()
        for dirpath in self._dataset_path:
            if os.path.isfile(dirpath):
                filenames = [dirpath]
            else:
                filenames = find_data(dirpath, minx, miny, maxx, maxy)

            raster.mosaic(filenames)

            if not elevation:
                elevation = raster.read()
            else:
                elevation = alpha_blend(elevation, raster.read(), 0.8)

        aspect, slope = aspect_and_slope(elevation, self._zfactor, self._scale)
        diffuse = hillshade(aspect, slope, self._aziumth, 35)
        specular = hillshade(aspect, slope, self._aziumth, 85)

        aspect, slope = aspect_and_slope(elevation, self._zfactor / 2.0, self._scale)
        detail = hillshade(aspect, slope, self._aziumth, 65)

        raster.close()

        images = {
            'diffuse': (array2img(diffuse), '.jpg'),
            'detail': (array2img(detail), '.jpg'),
            'specular': (array2img(specular), '.jpg'),
        }

        hillshading = self._composer.compose(images)

        return hillshading
