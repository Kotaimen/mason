# -*- coding:utf-8 -*-
'''
Created on Oct 11, 2012

@author: ray
'''

from .core import Pyramid, Metadata, metatile_fission, buffer_crop, Tile, Format
from .renderer import create_render_node, MetaTileContext
from .tilestorage import create_tilestorage


#===============================================================================
# Exceptions
#===============================================================================
class RootConfigNotFound(Exception):
    pass


class PyramidConfigNotFound(Exception):
    pass


class MetadataConfigNotFound(Exception):
    pass


class RendererConfigNotFound(Exception):
    pass


class RenderNodeConfigNotFound(Exception):
    pass


class InvalidStorageConfig(Exception):
    pass


#===============================================================================
# Mason Configuration
#===============================================================================
class MasonConfig(object):

    def __init__(self, filename):
        global_vars, local_vars = {}, {}
        execfile(filename, global_vars, local_vars)

        self._node_cfg = dict()
        for name, val in local_vars.items():
            if not self._is_node_cfg(val):
                continue
            self._node_cfg[name] = val

    def get_node_cfg(self, name):
        return self._node_cfg.get(name)

    def _is_node_cfg(self, val):
        return isinstance(val, dict) and 'prototype' in val


#===============================================================================
# Mason Renderer
#===============================================================================
class MasonRenderer(object):

    ROOT_NODE_NAME = 'ROOT'

    def __init__(self, mason_config, mode=None):
        self._mason_cfg = mason_config
        self._mode = mode or 'dryrun'  # default is 'dryrun'

        root_cfg = mason_config.get_node_cfg('ROOT')
        if not root_cfg:
            raise RootConfigNotFound

        pyramid_cfg = root_cfg.get('pyramid')
        if not pyramid_cfg:
            raise PyramidConfigNotFound
        else:
            # Replace format string with real Format object
            if 'format' in pyramid_cfg:
                pyramid_cfg['format'] = Format.from_name(pyramid_cfg['format'])

        metadata_cfg = root_cfg.get('metadata')
        if not metadata_cfg:
            raise MetadataConfigNotFound

        renderer_cfg = root_cfg.get('renderer')
        if not renderer_cfg:
            raise RendererConfigNotFound

        storage_cfg = root_cfg.get('storage')

        self._pyramid = self._create_pyramid(pyramid_cfg)
        self._metadata = self._create_metadata(metadata_cfg)

        self._renderer = self._create_renderer(
            renderer_cfg,
            self._pyramid,
            self._metadata)
        self._storage = self._create_storage(
            storage_cfg,
            self._pyramid,
            self._metadata)

    @property
    def pyramid(self):
        return self._pyramid

    @property
    def metadata(self):
        return self._metadata

    def has_tile(self, tile_index):
        return self._storage.has(tile_index)

    def has_metatile(self, metatile_index):
        tile_indexes = metatile_index.fission()
        return self._storage.has_all(tile_indexes)

    def render_tile(self, tile_index):
        if self._mode in ('hybrid', 'readonly'):
            tile = self._storage.get(tile_index)
            if tile or self._mode == 'readonly':
                return tile

        z, x, y = tile_index.coord
        metatile_index = self._pyramid.create_metatile_index(z, x, y, 1)
        metatile = self.render_metatile(metatile_index)

        data = buffer_crop(metatile.data,
                           metatile.index.buffered_tile_size,
                           metatile.index.buffer,
                           metatile.format)
        tile = Tile.from_tile_index(tile_index, data, metatile.format,
                                    metatile.mtime)

        if self._mode in ('hybrid', 'overwrite'):
            self._storage.put(tile)

        return tile

    def render_metatile(self, metatile_index):
        context = MetaTileContext(metatile_index, self._mode)
        metatile = self._renderer.render(context)

        if self._mode in ('hybrid', 'overwrite'):
            tile_indexes = metatile_index.fission()
            if self._mode == 'overwrite' or \
                    not self._storage.has_all(tile_indexes):
                tiles = metatile_fission(metatile)
                self._storage.put_multi(tiles)

        self._renderer.clean_up()
        return metatile

    def close(self):
        self._renderer.close()

    def _create_pyramid(self, pyramid_cfg):
        return Pyramid(**pyramid_cfg)

    def _create_metadata(self, metadata_cfg):
        return Metadata.make_metadata(**metadata_cfg)

    def _create_renderer(self, renderer_name, pyramid, metadata):
        renderer_cfg = self._mason_cfg.get_node_cfg(renderer_name)
        if not renderer_cfg:
            raise RenderNodeConfigNotFound(renderer_name)

        cfg = dict(renderer_cfg)
        child_names = cfg.pop('sources', list())
        if isinstance(child_names, str):
            child_names = [child_names, ]

        prototype = cfg.pop('prototype')
        cache_cfg = cfg.pop('cache', None)
        keep_cache = cfg.pop('keep_cache', True)

        cache = self._create_storage(cache_cfg, pyramid, metadata)

        render_node = create_render_node(prototype,
                                         renderer_name,
                                         cache=cache,
                                         **cfg)
        render_node.keep_cache = keep_cache

        for name in child_names:
            child_node = self._create_renderer(name, pyramid, metadata)
            render_node.add_child(child_node)

        return render_node

    def _create_storage(self, storage_cfg, pyramid, metadata):
        if not storage_cfg:
            storage_cfg = dict(prototype='null')

        cfg = dict(storage_cfg)
        prototpye = cfg.pop('prototype', None)
        if not prototpye:
            raise InvalidStorageConfig(repr(storage_cfg))

        return create_tilestorage(prototpye, pyramid, metadata, **cfg)


#==============================================================================
# Facade
#==============================================================================
def create_render_tree_from_config(config_file, option):
    """ Create a render tree from given configuration file.

    option:
        1.mode can be one of following:
        - default: write to cache after render
        - overwrite: render and overwrite any existing cache
        - readonly: only read from cache
        - dryrun: always render but does not write to cache

        2.reload can be true or false
        - true: reload configurations, such as mapnik stylesheet.
        - false: load configurations only at start up.

    """
    config = MasonConfig(config_file)
    return MasonRenderer(config, **option)
