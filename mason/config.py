'''
Created on Apr 28, 2012

@author: Kotaimen
'''


def create_render_tree_from_config(config_file, mode='default'):
    """ Create a render tree from given configuration file

    mode can be one of following:
    - default: write to cache after render
    - overwrite: render and overwrite any existing cache
    - readonly: only read from cache
    - dryrun: always render but does not write to cache
    """
    raise NotImplementedError




