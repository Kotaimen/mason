'''
Created on Apr 28, 2012

@author: Kotaimen
'''

from .mason import Mason
from .layer import Layer, create_layer


from pprint import pprint


def create_mason_from_config(config_file, mode):
    """ Load a configuration file and setup Mason (Tile Layer Manager)

    """

    # Just execute the configuration file in local context,
    # XXX: Also supports JSON?
    globals, locals = {}, {}
    execfile(config_file, globals, locals)

    layers_config = locals['LAYERS']

#    print pprint(layers_config)

    mason = Mason()

    for layer_config in layers_config:
        # Inject "mode" parameter into layer configuration
        layer_config = dict(layer_config)
        layer_config['mode'] = mode
        layer = create_layer(**layer_config)
        mason.add_layer(layer)

    return mason
