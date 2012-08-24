'''
Created on Apr 28, 2012

@author: Kotaimen
'''

from .mason import Mason
from .namespace import Namespace, create_namespace


from pprint import pprint


def create_mason_from_config(config_file, mode):
    """ Load a configuration file and setup Mason (Tile Namespace Manager)

    """

    # Just execute the configuration file in local context,
    # XXX: Also supports JSON?
    globals, locals = {}, {}
    execfile(config_file, globals, locals)

    namespace_configs = locals['LAYERS']

#    print pprint(namespace_configs)

    mason = Mason()

    for namespace_config in namespace_configs:
        # Inject "mode" parameter into namespace configuration
        namespace_config = dict(namespace_config)
        namespace_config['mode'] = mode
        namespace = create_namespace(**namespace_config)
        mason.add_namespace(namespace)

    return mason
