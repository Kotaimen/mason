'''
Created on Jun 3, 2013

@author: ray
'''
from ..tilestorage import create_tilestorage
from ..core import Format
from . import nodeconfig
from . import node


def create_null_node(name, **params):
    return node.NullRenderNode(name)


def create_hillshading_node(name, **params):
    config = nodeconfig.HillShadingNodeConfig(name, **params)
    return node.HillShadingRenderNode(config)


def create_colorrelief_node(name, **params):
    config = nodeconfig.ColorReliefNodeConfig(name, **params)
    return node.ColorReliefRenderNode(config)


def create_storage_node(name, **params):
    config = nodeconfig.StorageNodeConfig(name, **params)
    return node.StorageRenderNode(config)


def create_imagemagick_node(name, **params):
    config = nodeconfig.ImageMagicComposerNodeConfig(name, **params)
    return node.ImageMagicRenderNode(config)


def create_mapnik_node(name, **params):
    params['prototype'] = 'mapnik'
    config = nodeconfig.MapnikNodeConfig(name, **params)
    return node.CartographerRenderNode(config)


def create_raster_node(name, **params):
    params['prototype'] = 'dataset'
    config = nodeconfig.RasterNodeConfig(name, **params)
    return node.CartographerRenderNode(config)


def create_homebrewhillshade(name, **params):
    params['prototype'] = 'shaderelief'
    config = nodeconfig.HomeBrewHillShadingNodeConfig(name, **params)
    return node.CartographerRenderNode(config)


class RenderNodeFactory(object):

    REGISTRY = {
                'node.null': create_null_node,
                'node.hillshading': create_hillshading_node,
                'node.colorrelief': create_colorrelief_node,
                'node.storage': create_storage_node,
                'node.imagemagick': create_imagemagick_node,
                'node.mapnik': create_mapnik_node,
                'node.raster': create_raster_node,
                'node.homebrewhillshade': create_homebrewhillshade,
                }

    def __call__(self, name, **params):
        params = dict(params)
        prototype = params.pop('prototype')
        if prototype is None:
            raise RuntimeError('[%s] node prototype is missing' % name)

        creator = self.REGISTRY.get(prototype)
        if creator is None:
            raise RuntimeError('[%s] unknown prototype "%s" !' % (name, prototype))

        node = creator(name, **params)
        return node


def create_render_cache(metadata, pyramid, cache_config):
    if not cache_config:
        cache_config = dict(prototype='null')

    config = dict(cache_config)
    prototpye = config.pop('prototype', None)
    if prototpye not in ('null', 'metacache'):
        raise RuntimeError('invalid cache prototype %s' % prototpye)

    format_name = config.pop('data_format', None)
    if format_name:
        data_format = Format.from_name(format_name)
        pyramid = pyramid.clone(format=data_format)

    return create_tilestorage(prototpye, pyramid, metadata, **config)


#===============================================================================
# Node Creator
#===============================================================================
def create_render_node(name, metadata, pyramid, **params):
    # initialize cache
    params = dict(params)
    cache_config = params.get('cache', None)
    cache = create_render_cache(metadata, pyramid, cache_config)
    params['cache'] = cache

    return RenderNodeFactory()(name, **params)
