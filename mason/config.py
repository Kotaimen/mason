# -*- coding:utf-8 -*-
'''
Created on Oct 11, 2012

@author: ray
'''
import sys
import networkx as nx
from .core import Pyramid, Metadata, Format, metatile_fission
from .tilestorage import create_tilestorage
from .renderer import RendererFactory


class RenderConfigError(Exception):
    pass


#==============================================================================
# Create cached storage
#==============================================================================
def build_cache_storage(cache_config, pyramid, metadata):
    """ create cache storage from cache configuration """

    if not cache_config:
        cache_config = dict(prototype='null')

    cache_config = dict(cache_config)

    prototype = cache_config.pop('prototype', None)
    if not prototype:
        raise RuntimeError('storage prototype is missing.')

    # inject data format for every storage
    format_name = cache_config.pop('data_format', None)
    if format_name:
        data_format = Format.from_name(format_name)
        pyramid = pyramid.clone(format=data_format)

    storage = create_tilestorage(\
                   prototype,
                   pyramid,
                   metadata,
                   **cache_config
                   )

    return storage


#==============================================================================
# Render Tree
#==============================================================================
class RenderTree(object):

    def __init__(self, config, mode='default', reload=False):

        self._mode = mode
        self._reload = reload
        self._factory = RendererFactory(mode)

        # create renderer configuration tree
        self._pyramid = self._create_pyramid(config)
        self._metadata = self._create_metadata(config)
        self._renderer = self._create_renderer(
                               config,
                               self._pyramid,
                               self._metadata)
        self._renderer_cache = build_cache_storage(
                               config.renderer_cache_config,
                               self._pyramid,
                               self._metadata)

    def _create_pyramid(self, config):
        pyramid_config = config.pyramid_config
        if 'format' in pyramid_config:
            format_name = pyramid_config['format']
            pyramid_config['format'] = Format.from_name(format_name)
        return Pyramid(**pyramid_config)

    def _create_metadata(self, config):
        metadata_config = config.metadata_config
        return Metadata.make_metadata(**metadata_config)

    def _create_renderer(self, config, pyramid, metadata):
        render_tree = nx.DiGraph()
        for node in config.render_nodes():
            node_name, node_attr = node
            render_tree.add_node(node_name, **node_attr)

        for edge in config.render_edges():
            start, end = edge
            render_tree.add_edge(start, end)

        # create renderer
        render_nodes = dict()
        for node in nx.dfs_postorder_nodes(render_tree, config.renderer):
            node_name, node_config = node, render_tree.node[node]

            try:
                # prototype
                prototype = node_config['prototype']

                # attributes
                attrdict = node_config['attrdict']
                # inject reload option for mapnik
                if prototype == 'datasource.mapnik':
                    attrdict['force_reload'] = self._reload

                # sources
                source_nodes = list()
                for node in node_config['sources']:
                    if node not in render_nodes:
                        raise RuntimeError('unknown source %s' % node)
                    source_nodes.append(render_nodes[node])

                # cache
                cache = node_config['cache']
                storage = build_cache_storage(cache, pyramid, metadata)

                renderer = self._factory(prototype,
                                         source_nodes,
                                         storage,
                                         **attrdict)

                render_nodes[node_name] = renderer

            except Exception as e:
                raise RuntimeError('config "%s": %s' % (node_name, str(e)))

        return render_nodes[config.renderer]

    @property
    def pyramid(self):
        return self._pyramid

    @property
    def metadata(self):
        return self._metadata

    def render(self, metatile_index):
        metatile = self._renderer.render(metatile_index)
        if self._renderer_cache and self._mode in ['default', 'overwrite']:
            tile_indexes = metatile_index.fission()
            if self._mode == 'overwrite' or \
                    not self._renderer_cache.has_all(tile_indexes):
                tiles = metatile_fission(metatile)
                self._renderer_cache.put_multi(tiles)

        return metatile

    def show(self):
        nx.write_edgelist(self._graph, sys.stdout)

    def close(self):
        self._renderer.close()


#==============================================================================
# Render Configuration Parser
#==============================================================================
class RenderConfigParser(object):

    ROOT_NAME = 'ROOT'

    def __init__(self):
        self._pyramid_config = dict()
        self._metadata_config = dict()
        self._cache_config = dict()
        self._renderer = None

        self._nodes = dict()
        self._edges = list()

    def read(self, filename):
        global_vars, local_vars = {}, {}
        execfile(filename, global_vars, local_vars)

        config = dict(local_vars)

        self._parse_root(config)
        self._parse_nodes_and_edges(config)

    def _parse_root(self, config):
        # parse root configuration
        root_config = config.get(self.ROOT_NAME, None)
        if not root_config:
            raise RenderConfigError('missing "root" config')

        # pyramid configuration
        pyramid = root_config.get('pyramid', None)
        if not pyramid:
            raise RenderConfigError('missing "pyramid" config in root')

        # metadata configuration
        metadata = root_config.get('metadata', None)
        if 'metadata' not in root_config:
            raise RenderConfigError('missing "metadata" config in root')

        # renderer configuration
        renderer = root_config.get('renderer', None)
        if 'renderer' not in root_config:
            raise RenderConfigError('missing "renderer" node in root')

        # cache configuration
        cache = root_config.get('cache', None)

        self._pyramid_config = pyramid
        self._metadata_config = metadata
        self._renderer = renderer
        self._cache_config = cache

    def _parse_nodes_and_edges(self, config):
        # parse configurations of render nodes
        self._nodes = dict()
        for name, val in config.items():
            # a valid render node configuration should
            # be a dictionary with prototype
            if not isinstance(val, dict) or 'prototype' not in val:
                continue

            node_config = dict(val)

            # node prototype
            prototype = node_config.pop('prototype', None)

            # node sources
            sources = node_config.pop('sources', tuple())
            if isinstance(sources, str):
                sources = (sources,)
            sources = tuple(sources)

            # node cache
            cache = node_config.pop('cache', None)

            self._nodes[name] = dict(prototype=prototype,
                                     sources=sources,
                                     cache=cache,
                                     attrdict=node_config)

        # parse configurations of edges
        self._edges = list()
        for name, config in self._nodes.items():
            start = name
            for end in config['sources']:
                if end not in self._nodes:
                    raise RenderConfigError(
                            'Unkonwn reference: %s->%s' % (start, end))
                self._edges.append((start, end))

    @property
    def pyramid_config(self):
        return self._pyramid_config

    @property
    def metadata_config(self):
        return self._metadata_config

    @property
    def renderer_cache_config(self):
        return self._cache_config

    @property
    def renderer(self):
        return self._renderer

    def render_nodes(self):
        return self._nodes.items()

    def render_edges(self):
        return self._edges


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
    config = RenderConfigParser()
    config.read(config_file)
    return RenderTree(config, **option)
