__author__ = 'Kotaimen <kotaimen.c@gmail.com>, Ray <gliese.q@gmail.com>'
version = (0, 9, 4)
__version__ = '.'.join(map(str, version))


from .mason import Mason
from .config import create_render_tree_from_config
