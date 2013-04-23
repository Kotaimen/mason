# -*- coding:utf-8 -*-
'''
mason.renderer.node

Created on Mar 17, 2013
@author: ray
'''
import time
from ..cartographer import Mapnik, RasterDataset, ShadeRelief
from ..composer import ImageMagickComposer
from ..tilestorage import attach_tilestorage
from ..core import MetaTile, Format
from ..utils import TempFile, gdal_hillshading, gdal_colorrelief
from .tree import RenderNode, RenderContext
from .cache import RenderCache


#===============================================================================
# Exceptions
#===============================================================================
class SourceNotFound(Exception):
    pass


class GDALProcessError(Exception):
    pass

#===============================================================================
# Metatile Context
#===============================================================================
class MetaTileContext(RenderContext):

    def __init__(self, metatile_index, mode=None):
        mode = mode or 'dryrun'
        assert mode in ('hybrid', 'readonly', 'overwrite', 'dryrun')
        self._metatile_index = metatile_index
        self._mode = mode

    @property
    def mode(self):
        return self._mode

    @property
    def metatile_index(self):
        return self._metatile_index


#===============================================================================
# Metatile Render Node (Base Class)
#===============================================================================
class MetaTileRenderNode(RenderNode):

    def __init__(self, name, cache=None):
        RenderNode.__init__(self, name)
        self._cache = RenderCache(cache)
        self._keep_cache = True

    @property
    def keep_cache(self):
        return self._keep_cache

    @keep_cache.setter
    def keep_cache(self, val):
        self._keep_cache = val

    def erase(self, metatile_index):
        for child in self._children.values():
            child.erase(metatile_index)
        if not self._keep_cache:
            self._cache.delete(metatile_index)

    def render(self, context):
        assert isinstance(context, MetaTileContext)
        return RenderNode.render(self, context)

    def _render_imp(self, context, sources):
        metatile_index = context.metatile_index
        metatile_sources = sources

        # get metatile from cache
        if context.mode in ('hybrid', 'readonly'):
            metatile = self._cache.get(metatile_index)
            if metatile or context.mode == 'readonly':
                return metatile

        # render a metatile
        metatile = self._render_metatile(metatile_index, metatile_sources)

        # cache the new metatile
        if context.mode in ('overwrite', 'hybrid'):
            self._cache.put(metatile)

        return metatile

    def _render_metatile(self, metatile_index, metatile_sources):
        raise NotImplementedError


#===============================================================================
# GDAL Render Node (Base Class)
#===============================================================================
class GDALRenderNode(MetaTileRenderNode):

    def __init__(self, name, cache=None):
        MetaTileRenderNode.__init__(self, name, cache)

    def _render_metatile(self, metatile_index, metatile_sources):
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
            self._process(metatile_index, source, target)

        except Exception as e:
            raise GDALProcessError('%s: %s' % (self.name, str(e)))
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

    def _process(self, source, target):
        raise NotImplementedError


#===============================================================================
# Hill Shading Render Node
#===============================================================================
class HillShadingRenderNode(GDALRenderNode):

    def __init__(self, name,
                 zfactor=1,
                 scale=1,
                 altitude=45,
                 azimuth=315,
                 cache=None):
        GDALRenderNode.__init__(self, name, cache)
        self._zfactor = zfactor
        self._scale = scale
        self._altitude = altitude
        self._azimuth = azimuth

    def _process(self, metatile_index, source, target):
        z, x, y = metatile_index.coord
        # get parameters
        zfactor = self._zfactor
        if isinstance(zfactor, list):
            zfactor = zfactor[z] if z < len(zfactor) else zfactor[-1]

        scale = self._scale
        if isinstance(scale, list):
            scale = scale[z] if z < len(scale) else scale[-1]

        altitude = self._altitude
        if isinstance(altitude, list):
            altitude = altitude[z] if z < len(altitude) else altitude[-1]

        azimuth = self._azimuth
        if isinstance(azimuth, list):
            azimuth = azimuth[z] if z < len(azimuth) else azimuth[-1]

        # call gdal subprocess
        src = source.filename
        dst = target.filename
        gdal_hillshading(src, dst, zfactor, scale, altitude, azimuth)


class HomeBrewHillShade(GDALRenderNode):

    def __init__(self, name,
                 dataset_path,
                 zfactor=1,
                 scale=1,
                 altitude=45,
                 azimuth=315,
                 cache=None):
        GDALRenderNode.__init__(self, name, cache)
        self._dataset_path = dataset_path
        self._zfactor = zfactor
        self._scale = scale
        self._altitude = altitude
        self._azimuth = azimuth

    def _render_metatile(self, metatile_index, metatile_sources):
        assert len(metatile_sources) == 0

        z, x, y = metatile_index.coord

        zfactor = self._zfactor
        if isinstance(zfactor, list):
            zfactor = zfactor[z] if z < len(zfactor) else zfactor[-1]

        scale = self._scale
        if isinstance(scale, list):
            scale = scale[z] if z < len(scale) else scale[-1]

        altitude = self._altitude
        if isinstance(altitude, list):
            altitude = altitude[z] if z < len(altitude) else altitude[-1]

        azimuth = self._azimuth
        if isinstance(azimuth, list):
            azimuth = azimuth[z] if z < len(azimuth) else azimuth[-1]

        dataset_path = self._dataset_path
        if isinstance(dataset_path, list):
            dataset_path = dataset_path[z] if z < len(dataset_path) else dataset_path[-1]

        self._rasterdataset = ShadeRelief(dataset_path,
                                          zfactor=zfactor,
                                          scale=scale,
                                          azimuth=azimuth,
                                          altitude=altitude)

        envelope = metatile_index.buffered_envelope.make_tuple()
        width = height = metatile_index.buffered_tile_size
        size = (width, height)
        data_stream = self._rasterdataset.render(envelope, size)
        try:
            data_format = Format.from_name(self._rasterdataset.output_format)
            mtime = time.time()
            metatile = MetaTile.from_tile_index(metatile_index,
                                                data_stream.getvalue(),
                                                data_format,
                                                mtime)
        finally:
            data_stream.close()

        return metatile


#===============================================================================
# Color Relief Render Node
#===============================================================================
class ColorReliefRenderNode(GDALRenderNode):

    def __init__(self, name, color_context, cache=None):
        GDALRenderNode.__init__(self, name, cache)
        self._color_context = color_context

    def _process(self, metatile_index, source, target):
        # call gdal subprocess
        src = source.filename
        dst = target.filename
        gdal_colorrelief(src, dst, self._color_context)


#===============================================================================
# Storage Render Node
#===============================================================================
class StorageRenderNode(MetaTileRenderNode):

    def __init__(self, name, storage_cfg, default=None, cache=None):
        MetaTileRenderNode.__init__(self, name, cache)
        self._storage = attach_tilestorage(**storage_cfg)
        if default:
            with open(default, 'rb') as fp:
                self._default = fp.read()

    def _render_metatile(self, metatile_index, metatile_sources):
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


#===============================================================================
# Mapnik Render Node
#===============================================================================
class MapnikRenderNode(MetaTileRenderNode):

    def __init__(self, name, cache=None, **mapnik_cfg):
        MetaTileRenderNode.__init__(self, name, cache)
        self._mapniker = Mapnik(**mapnik_cfg)

    def _render_metatile(self, metatile_index, metatile_sources):
        assert len(metatile_sources) == 0

        envelope = metatile_index.buffered_envelope.make_tuple()
        width = height = metatile_index.buffered_tile_size
        size = (width, height)
        data_stream = self._mapniker.render(envelope, size)
        try:
            data_format = Format.from_name(self._mapniker.output_format)
            mtime = time.time()
            metatile = MetaTile.from_tile_index(metatile_index,
                                                data_stream.getvalue(),
                                                data_format,
                                                mtime)
        finally:
            data_stream.close()

        return metatile


#===============================================================================
# Raster Render Node
#===============================================================================
class RasterRenderNode(MetaTileRenderNode):

    def __init__(self, name, cache=None, **dataset_cfg):
        MetaTileRenderNode.__init__(self, name, cache)
        self._raw_cfg = dataset_cfg
        self._dataset = None

    def _init_config(self, metatile_index, dataset_cfg):
        z, x, y = metatile_index.coord

        dataset_cfg = dict(dataset_cfg)
        ds_path = dataset_cfg['dataset_path']
        if isinstance(ds_path, list):
            ds_path = ds_path[z] if z < len(ds_path) else ds_path[-1]
        dataset_cfg['dataset_path'] = ds_path

        return dataset_cfg

    def _render_metatile(self, metatile_index, metatile_sources):
        assert len(metatile_sources) == 0

        dataset_cfg = self._init_config(metatile_index, self._raw_cfg)
        self._dataset = RasterDataset(**dataset_cfg)

        envelope = metatile_index.buffered_envelope.make_tuple()
        width = height = metatile_index.buffered_tile_size
        size = (width, height)
        data_stream = self._dataset.render(envelope, size)
        try:
            data_format = Format.from_name(self._dataset.output_format)
            mtime = time.time()
            metatile = MetaTile.from_tile_index(metatile_index,
                                                data_stream.getvalue(),
                                                data_format,
                                                mtime)
        finally:
            data_stream.close()

        return metatile


#===============================================================================
# ImageMagic Render Node
#===============================================================================
class ImageMagicRenderNode(MetaTileRenderNode):

    def __init__(self, name, format, command, command_params=None, cache=None):
        MetaTileRenderNode.__init__(self, name, cache)
        self._command = command
        self._command_params = command_params

        self._composer = ImageMagickComposer(format)

    def _init_command(self, metatile_index):
        if not self._command_params:
            return self._command

        z, x, y = metatile_index.coord
        params = dict()
        for name, param in self._command_params.items():
            val = param
            if isinstance(param, list):
                val = param[z] if z < len(param) else param[-1]
            params[name] = val

        return self._command % params

    def _render_metatile(self, metatile_index, metatile_sources):
        assert len(metatile_sources) >= 1

        images = dict()
        for name, m in metatile_sources.items():
            images[name] = (m.data, m.format.extension)

        command = self._init_command(metatile_index)
        self._composer.setup_command(command)
        data_stream = self._composer.compose(images)
        try:
            data_format = Format.from_name(self._composer.output_format)
            mtime = time.time()

            metatile = MetaTile.from_tile_index(metatile_index,
                                                data_stream.getvalue(),
                                                data_format,
                                                mtime)
        finally:
            data_stream.close()
        return metatile
