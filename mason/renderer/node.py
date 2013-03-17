# -*- coding:utf-8 -*-
'''
mason.renderer.node

Created on Mar 17, 2013
@author: ray
'''
import time
from ..cartographer import gdal_hillshading, gdal_colorrelief
from ..core import MetaTile, Format
from ..utils import TempFile
from .tree import RenderNode, RenderContext, MissingSource


#===============================================================================
# Metatile Context
#===============================================================================
class MetaTileContext(RenderContext):

    def __init__(self, metatile_index):
        RenderContext.__init__(self)
        self._metatile_index = metatile_index

    @property
    def metatile_index(self):
        return self._metatile_index


#===============================================================================
# Metatile Render Node
#===============================================================================
class MetaTileRenderNode(RenderNode):

    """
    
    """

    def __init__(self, name, source_names):
        RenderNode.__init__(self, name, source_names)

    def render(self, context):
        # get metatile index
        metatile_index = context.metatile_index
        metatile_pool = context.source_pool

        # get metatile sources
        metatile_sources = dict()
        for name in self._source_names:
            metatile_key = self.__metatile_key__(name, metatile_index)
            metatile_source = metatile_pool.get(metatile_key)
            if not metatile_source:
                raise MissingSource(metatile_key)
            metatile_sources[name] = metatile_source

        # render metatile
        result = self.__render__(metatile_index, metatile_sources)

        # put result back to the pool
        result_key = self.__metatile_key__(self._name, metatile_index)
        metatile_pool.put(result_key, result)
        return result

    def __metatile_key__(self, name, metatile_index):
        return name + repr(metatile_index)

    def __render__(self, metatile_index, metatile_sources):
        raise NotImplementedError


class GDALRenderNode(MetaTileRenderNode):

    def __init__(self, name, source_names):
        MetaTileRenderNode.__init__(self, name, source_names)

    def __render__(self, metatile_index, metatile_sources):
        assert len(metatile_sources) == 1
        metatile = metatile_sources.values()[0]
        data = metatile.data
        data_format = metatile.format

        try:
            # create temporary files
            source = TempFile()
            target = TempFile()

            # write data to the source file
            source.write(data)

            # process
            self.__process__(metatile_index, source, target)

        except Exception as e:
            raise e
        else:
            # read data from target file
            data = target.read()
            data_format = metatile.format
            mtime = time.time()
            metatile = MetaTile.from_tile_index(metatile.index,
                                                data,
                                                data_format,
                                                mtime)
            return metatile
        finally:
            # close files
            source.close()
            target.close()

    def __process__(self, source, target):
        raise NotImplementedError


class HillShadingRenderNode(GDALRenderNode):

    def __init__(self, name, source_names,
                 zfactor=1,
                 scale=1,
                 altitude=45,
                 azimuth=315):
        GDALRenderNode.__init__(self, name, source_names)
        self._zfactor = zfactor
        self._scale = scale
        self._altitude = altitude
        self._azimuth = azimuth

    def __process__(self, metatile_index, source, target):
        z, x, y = metatile_index.coord
        # get parameters
        zfactor = self._zfactor
        zfactor = callable(zfactor) and zfactor(z, x, y) or zfactor

        scale = self._scale
        scale = callable(scale) and scale(z, x, y) or scale

        altitude = self._altitude
        altitude = callable(altitude) and altitude(z, x, y) or altitude

        azimuth = self._azimuth
        azimuth = callable(azimuth) and azimuth(z, x, y) or azimuth

        # call gdal subprocess
        src = source.filename
        dst = target.filename
        gdal_hillshading(src, dst, zfactor, scale, altitude, azimuth)


class ColorReliefRenderNode(GDALRenderNode):

    def __init__(self, name, source_names, color_context):
        GDALRenderNode.__init__(self, name, source_names)
        self._color_context = color_context

    def __process__(self, metatile_index, source, target):
        z, x, y = metatile_index.coord

        # get color context parameter
        color_ctx = self._color_context
        color_ctx = callable(color_ctx) and callable(z, x, y) or color_ctx

        # call gdal subprocess
        src = source.filename
        dst = target.filename
        gdal_colorrelief(src, dst, color_ctx)


class StorageRenderNode(MetaTileRenderNode):

    def __init__(self, name, storage_cfg):
        MetaTileRenderNode.__init__(self, name)
        self._storage = None

    def __render__(self, metatile_index, metatile_sources):
        assert len(metatile_sources) == 0
        metatile = self._storage.get(metatile_index)
        if metatile is None:
            if self._default is not None:
                return MetaTile.from_tile_index(
                    metatile_index,
                    self._default,
                    fmt=self._storage.pyramid.format)
            else:
                raise RuntimeError('no data found %s' % str(metatile_index))

        return metatile


class MapnikRenderNode(MetaTileRenderNode):

    def __init__(self, name, mapnik_cfg):
        MetaTileRenderNode.__init__(self, name, source_names=list())

    def __render__(self, metatile_index, metatile_sources):
        pass


class RasterRenderNode(MetaTileRenderNode):

    def __init__(self, name, dataset_cfg):
        MetaTileRenderNode.__init__(self, name, source_names=list())

    def __render__(self, metatile_index, metatile_sources):
        pass


class ImageMagicRenderNode(MetaTileRenderNode):

    def __init__(self, name, source_names, command):
        MetaTileRenderNode.__init__(self, name, source_names)

    def __render__(self, metatile_index, metatile_sources):
        pass
