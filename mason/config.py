'''
Created on Apr 28, 2012

@author: Kotaimen
'''

from .mason import Mason
from .layer import Layer, create_layer


def create_mason_from_config(config_file, mode):

    globals, locals = {}, {}
    execfile(config_file, globals, locals)
    layers_config = locals['LAYERS']

    mason = Mason(mode)

    for layer_config in layers_config:
        layer = create_layer(**layer_config)
        mason.add_layer(layer)

    return mason
