# -*- coding:utf-8 -*-
'''
mason.renderer.node

Created on Mar 17, 2013
@author: ray
'''
import time
from ..cartographer import CartographerFactory
from ..composer import ImageMagickComposer
from ..tilestorage import attach_tilestorage
from ..core import MetaTile, Format
from ..utils import TempFile, gdal_hillshading, gdal_colorrelief
from .base import MetaTileRenderNode, NullRenderNode


def create_metatile(metatile_index, data, data_format):
    mtime = time.time()
    metatile = MetaTile.from_tile_index(metatile_index,
                                        data,
                                        data_format,
                                        mtime)
    return metatile


#===============================================================================
# GDAL Render Node (Base Class)
#===============================================================================
class HillShadingRenderNode(MetaTileRenderNode):

    def __init__(self, config):
        MetaTileRenderNode.__init__(self, config)
        self._config = config

    def _render_impl(self, context, source_nodes):
        assert len(source_nodes) == 1

        metatile = source_nodes[0].render(context)
        if metatile is None:
            raise RuntimeError('[%s] source data not found.' % self.name)
        data = metatile.data
        data_format = metatile.format

        try:
            # create temporary files
            source = TempFile()
            target = TempFile()
            # write data to the source file
            source.write(data)
            # process
            params = self._config.get_params_from_context(context)
            gdal_hillshading(source.filename,
                             target.filename,
                             params['zfactor'],
                             params['scale'],
                             params['altitude'],
                             params['azimuth'])
            metatile = create_metatile(context.metatile_index,
                                       target.read(),
                                       data_format
                                       )
            return metatile
        finally:
            # clean up
            source.close()
            target.close()


#===============================================================================
# Color Relief Render Node
#===============================================================================
class ColorReliefRenderNode(MetaTileRenderNode):

    def __init__(self, config):
        MetaTileRenderNode.__init__(self, config)
        self._config = config

    def _render_impl(self, context, source_nodes):
        assert len(source_nodes) == 1

        metatile = source_nodes[0].render(context)
        if metatile is None:
            raise RuntimeError('[%s] source data not found.' % self.name)
        data = metatile.data
        data_format = metatile.format

        try:
            # create temporary files
            source = TempFile()
            target = TempFile()
            # write data to the source file
            source.write(data)
            # process
            params = self._config.get_params_from_context(context)
            gdal_colorrelief(source.filename,
                             target.filename,
                             params['color_context'])
            metatile = create_metatile(context.metatile_index,
                                       target.read(),
                                       data_format
                                       )
            return metatile
        finally:
            # clean up
            source.close()
            target.close()


#===============================================================================
# Storage Render Node
#===============================================================================
class StorageRenderNode(MetaTileRenderNode):

    def __init__(self, config):
        MetaTileRenderNode.__init__(self, config)
        self._config = config
        self._storage = None
        self._default = None

    def _render_impl(self, context, source_nodes):
        assert len(source_nodes) == 0

        if self._storage is None:
            params = self._config.get_params_from_context(context)
            self._storage = attach_tilestorage(**params['storage'])
            if params['default'] is not None:
                with open(params['default'], 'rb') as fp:
                    self._default = fp.read()

        metatile_index = context.metatile_index
        metatile = self._storage.get(metatile_index)

        # use default data
        if metatile is None and self._default is not None:
            data = self._default
            data_format = self._storage.pyramid.format
            metatile = create_metatile(metatile_index, data, data_format)

        return metatile


#===============================================================================
# Mapnik Render Node
#===============================================================================
class CartographerRenderNode(MetaTileRenderNode):

    def __init__(self, config):
        MetaTileRenderNode.__init__(self, config)
        self._config = config

    def _render_impl(self, context, source_nodes):
        assert len(source_nodes) == 0

        params = self._config.get_params_from_context(context)
        cartographer = CartographerFactory(**params)

        metatile_index = context.metatile_index
        envelope = metatile_index.buffered_envelope.make_tuple()
        width = height = metatile_index.buffered_tile_size
        size = (width, height)

        data_stream = cartographer.render(envelope, size)
        data = data_stream.getvalue()
        data_stream.close()

        data_format = Format.from_name(cartographer.output_format)
        metatile = create_metatile(metatile_index, data, data_format)
        return metatile


#===============================================================================
# ImageMagic Render Node
#===============================================================================
class ImageMagicRenderNode(MetaTileRenderNode):

    def __init__(self, config):
        MetaTileRenderNode.__init__(self, config)
        self._config = config

    def _render_impl(self, context, source_nodes):
        assert len(source_nodes) >= 1

        params = self._config.get_params_from_context(context)

        images = dict()
        for node in source_nodes:
            if node.name not in params['necessary_nodes']:
                continue
            metatile = node.render(context)
            images[node.name] = metatile.data, metatile.format.extension

        composer = ImageMagickComposer(params['format'])
        composer.setup_command(params['command'])

        data_stream = composer.compose(images)
        data = data_stream.getvalue()
        data_stream.close()

        data_format = Format.from_name(composer.output_format)
        metatile_index = context.metatile_index
        metatile = create_metatile(metatile_index, data, data_format)
        return metatile
