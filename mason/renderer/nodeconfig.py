# -*- coding:utf-8 -*-
'''
Created on May 30, 2013

@author: ray
'''
import re
from .base import MetaTileRenderConfig


class ParamNotFound(Exception):

    def __init__(self, node_name, param_name):
        self._node_name = node_name
        self._param_name = param_name

    def __str__(self):
        return '%s:%s' % (self._node_name, self._param_name)


class HillShadingNodeConfig(MetaTileRenderConfig):

    def __init__(self, name, **kwargs):
        MetaTileRenderConfig.__init__(self, name, **kwargs)

        parameters = dict(kwargs)
        self._zfactor = parameters.pop('zfactor', 1)
        self._scale = parameters.pop('scale', 1)
        self._altitude = parameters.pop('altitude', 45)
        self._azimuth = parameters.pop('azimuth', 315)

    def get_params_from_context(self, context):
        z, x, y = context.metatile_index.coord

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

        params = dict(
            zfactor=zfactor,
            scale=scale,
            altitude=altitude,
            azimuth=azimuth,
            )
        return params


class HomeBrewHillShadingNodeConfig(HillShadingNodeConfig):

    def __init__(self, name, **kwargs):
        HillShadingNodeConfig.__init__(self, name, **kwargs)

        parameters = dict(kwargs)
        self._dataset_path = parameters.pop('dataset_path', None)
        if self._dataset_path is None:
            raise ParamNotFound(name, 'dataset_path')

    def get_params_from_context(self, context):
        z, x, y = context.metatile_index.coord
        dataset_path = self._dataset_path
        if isinstance(dataset_path, list):
            dataset_path = dataset_path[z] if z < len(dataset_path) else dataset_path[-1]

        params = HillShadingNodeConfig.get_params_from_context(self, context)
        params['dataset_path'] = dataset_path
        params['prototype'] = 'shaderelief'
        return params


class ColorReliefNodeConfig(MetaTileRenderConfig):

    def __init__(self, name, **kwargs):
        MetaTileRenderConfig.__init__(self, name, **kwargs)

        parameters = dict(kwargs)
        self._color_context = parameters.get('color_context', None)
        if self._color_context is None:
            raise ParamNotFound(name, 'color_context')

    def get_params_from_context(self, context):
        params = dict(color_context=self._color_context)
        return params


class StorageNodeConfig(MetaTileRenderConfig):

    def __init__(self, name, **kwargs):
        MetaTileRenderConfig.__init__(self, name, **kwargs)

        parameters = dict(kwargs)
        self._default = parameters.pop('default', None)

        self._storage = parameters.pop('storage', None)
        if self._storage is None:
            raise ParamNotFound(name, 'storage')
        if not 'prototype' in self._storage:
            raise ParamNotFound(name, 'storage.prototype')

    def get_params_from_context(self, context):
        params = dict(default=self._default, storage=self._storage)
        return params


class MapnikNodeConfig(MetaTileRenderConfig):

    def __init__(self, name, **kwargs):
        MetaTileRenderConfig.__init__(self, name, **kwargs)

        parameters = dict(kwargs)
        self._theme = parameters.pop('theme', None)
        if self._theme is None:
            raise ParamNotFound(name, 'theme')
        self._projection = parameters.pop('projection', 'EPSG:3857')
        self._scale_factor = parameters.pop('scale_factor', 1.0)
        self._buffer_size = parameters.pop('buffer_size', 0)
        self._image_type = parameters.pop('image_type', 'png')
        self._image_parameters = parameters.pop('image_parameters', None)
        self._force_reload = parameters.pop('force_reload', False)

    def get_params_from_context(self, context):
        params = dict(
            prototype='mapnik',
            theme=self._theme,
            projection=self._projection,
            scale_factor=self._scale_factor,
            buffer_size=self._buffer_size,
            image_type=self._image_type,
            image_parameters=self._image_parameters,
            force_reload=self._force_reload,
            )
        return params


class RasterNodeConfig(MetaTileRenderConfig):

    def __init__(self, name, **kwargs):
        MetaTileRenderConfig.__init__(self, name, **kwargs)

        parameters = dict(kwargs)
        self._dataset_path = parameters.pop('dataset_path', None)
        if self._dataset_path is None:
            raise ParamNotFound(name, 'dataset_path')
        self._target_projection = parameters.pop('target_projection', 'EPSG:3857')
        self._target_nodata = parameters.pop('target_nodata', -32768)
        self._resample_method = parameters.pop('resample_method', None)
        self._work_memory = parameters.pop('work_memory', 1024)

    def get_params_from_context(self, context):
        z, x, y = context.metatile_index.coord

        dataset_path = self._dataset_path
        if isinstance(dataset_path, list):
            dataset_path = dataset_path[z] if z < len(dataset_path) else dataset_path[-1]

        params = dict(
            prototype='dataset',
            dataset_path=dataset_path,
            target_projection=self._target_projection,
            target_nodata=self._target_nodata,
            resample_method=self._resample_method,
            work_memory=self._work_memory,
            )

        return params


class ImageMagicComposerNodeConfig(MetaTileRenderConfig):

    def __init__(self, name, **kwargs):
        MetaTileRenderConfig.__init__(self, name, **kwargs)

        parameters = dict(kwargs)
        self._format = parameters.pop('format', None)
        if self._format is None:
            raise ParamNotFound(name, 'format')
        self._command = parameters.pop('command', None)
        if self._command is None:
            raise ParamNotFound(name, 'command')
        self._command_params = parameters.pop('command_params', None)

    def get_params_from_context(self, context):
        z, x, y = context.metatile_index.coord

        command = self._command
        if self._command_params:
            params = dict()
            for name, param in self._command_params.items():
                val = param
                if isinstance(param, list):
                    val = param[z] if z < len(param) else param[-1]
                params[name] = val

            command = command % params

        necessary_nodes = re.findall('\{\{(\w+)\}\}', command)
        params = dict(
            format=self._format,
            command=command,
            necessary_nodes=necessary_nodes
            )
        return params
