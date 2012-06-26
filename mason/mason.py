'''
Created on May 14, 2012

@author: Kotaimen
'''


class InvalidNamespace(Exception):
    pass


class TileNotFound(Exception):
    pass


class Mason(object):

    """ The "TileNamespaceManager", create and manage one or more Tile namespaces

    This is the "facade" class and hides details of tilesource/storage, and is
    supposed be used by server frontend and rendering scripts.

    Usually mason instance is created from configuration file using
    create_mason_from_config().
    """

    def __init__(self):
        self._namespaces = dict()

    def add_namespace(self, ns):
        """ Add a namespace to Mason """
        self._namespaces[ns.tag] = ns

    def del_namespace(self, tag):
        """ Remove existing namespace from Mason """
        del self._namespaces[tag]

    def get_namespace(self, tag):
        """ Returns a namespace object """
        return self._namespaces[tag]

    def craft_tile(self, alias, z, x, y):
        """ Craft a tile from tilesource or retrive one from tile storage.

        Returns a tuple of (data, metatdata).  data is a bytes array of tile
        data (usually an image), metadata is a dict of key-value pairs.
        """
        try:
            namespace = self._namespaces[alias]
        except KeyError:
            raise InvalidNamespace(alias)

        tile = namespace.get_tile(z, x, y)
        if tile is None:
            raise TileNotFound('%s/%d/%d/%d' % (alias, z, x, y))

        return tile.data, tile.metadata

    def get_namespaces(self):
        """ Get a list of tile aliases """
        return self._namespaces.keys()

    def get_namespace_metadata(self, alias):
        """ Get namespace metadata, return empty dict if the namespace
            does not exist
        """
        try:
            return self._namespaces[alias].metadata
        except KeyError:
            return {}

    def close(self):
        for namespace in self._namespaces.itervalues():
            namespace.close()
