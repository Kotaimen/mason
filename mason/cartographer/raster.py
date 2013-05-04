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

        # shared file handler
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

        source = create_vrt_from_filenames(filenames)
        if not source:
            return False

        source_proj = source.GetProjection()
        source_geotransform = source.GetGeoTransform()
        source_size = source.RasterXSize, source.RasterYSize

        src_ref = GeoReference(source_proj, source_geotransform, source_size)
        dst_ref = self._georeference

        # figure out resample method
        src_minx, src_miny, src_maxx, src_maxy = src_ref.envelope

        fr_srs = osr.SpatialReference()
        fr_srs.ImportFromWkt(src_ref.project)
        to_srs = osr.SpatialReference()
        to_srs.ImportFromWkt(dst_ref.project)
        transformer = osr.CoordinateTransformation(fr_srs, to_srs)
        src_minx, src_miny, _z = transformer.TransformPoint(src_minx, src_miny)
        src_maxx, src_maxy, _z = transformer.TransformPoint(src_maxx, src_maxy)

        # resy < 0
        org_width = source.RasterXSize
        org_height = source.RasterYSize
        proj_width = (src_maxx - src_minx) / dst_ref.resx
        proj_height = (src_maxy - src_miny) / dst_ref.resy

        zoom_ratio = min(proj_width / org_width, proj_height / org_height)
        resample = None
        if zoom_ratio < 0.5:
            resample = gdalconst.GRA_Cubic
        elif zoom_ratio > 1.2:
            resample = gdalconst.GRA_CubicSpline
        else:
            resample = gdalconst.GRA_Bilinear

        ret = gdal.ReprojectImage(source,
                                  self._raster,
                                  source_proj,
                                  dst_ref.project,
                                  resample,
                                  )
        # close source data
        source = None
        return gdalconst.CE_Failure != ret

    def close(self):
        self._raster = None


def create_vrt_from_filenames(filenames):

    if not filenames:
        return None

    sample = FileRaster(filenames[0])
    sample_ref = sample.georeference

    proj = sample_ref.project
    minx, miny, maxx, maxy = sample_ref.envelope
    resx, resy = sample_ref.resx, sample_ref.resy

    sample.close()

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

        source.close()

    width = int((maxx - minx) / resx + 0.5)
    height = int((maxy - miny) / resy + 0.5)
    geotransform = minx, resx, 0, maxy, 0, -resy

    driver = gdal.GetDriverByName('VRT')
    vrt = driver.Create('', width, height, 1, gdalconst.GDT_Float64)
    vrt.SetGeoTransform(geotransform)
    vrt.SetProjection(proj)

    band = vrt.GetRasterBand(1)
    band.SetNoDataValue(-32768)

    metadata = band.GetMetadata()
    for filename in filenames:
        xml = create_vrt_source(vrt, filename)
        if not xml:
            continue
        metadata['source_%d' % len(metadata)] = xml
    band.SetMetadata(metadata, 'vrt_sources')

    return vrt


def create_vrt_source(vrt, filename):

    source = gdal.OpenShared(filename, gdalconst.GA_ReadOnly)
    if not source:
        raise Exception('Source file %s not found' % filename)

    projection = source.GetProjection()
    geotransform = source.GetGeoTransform()
    size = (source.RasterXSize, source.RasterYSize)

    src_ref = GeoReference(projection, geotransform, size)

    dst_geotransform = vrt.GetGeoTransform()
    dst_project = vrt.GetProjection()
    dst_size = vrt.RasterXSize, vrt.RasterYSize

    dst_ref = GeoReference(dst_project, dst_geotransform, dst_size)
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

    s_offx = int((left - src_minx) / src_ref.resx + 0.5)
    s_offy = int((src_maxy - top) / src_ref.resy + 0.5)
    s_sizex = int((right - left) / src_ref.resx + 0.5)
    s_sizey = int((top - bottom) / src_ref.resy + 0.5)

    t_offx = int((left - dst_minx) / dst_ref.resx + 0.5)
    t_offy = int((dst_maxy - top) / dst_ref.resy + 0.5)
    t_sizex = int((right - left) / dst_ref.resx + 0.5)
    t_sizey = int((top - bottom) / dst_ref.resy + 0.5)

    src_rect = ElementTree.Element('SrcRect',
        xOff=str(s_offx),
        yOff=str(s_offy),
        xSize=str(s_sizex),
        ySize=str(s_sizey),
        )
    dst_rect = ElementTree.Element('DstRect',
        xOff=str(t_offx),
        yOff=str(t_offy),
        xSize=str(t_sizex),
        ySize=str(t_sizey),
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

    source = None
    return xml
