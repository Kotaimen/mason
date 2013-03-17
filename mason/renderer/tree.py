# -*- coding:utf-8 -*-
'''
Base class of MetaTile renderer

Created on March 14, 2013
@author: ray
'''
import networkx as nx


#===============================================================================
# Exceptions
#===============================================================================
class MissingSource(Exception):
    pass


class UnknownParentNode(Exception):
    pass


#===============================================================================
# Context
#===============================================================================
class Pool(object):

    def __init__(self):
        self._store = dict()

    def put(self, name, val):
        self._store[name] = val

    def get(self, name):
        return self._store.get(name)


class RenderContext(object):

    def __init__(self):
        self._pool = Pool()

    @property
    def source_pool(self):
        return self._pool


#===============================================================================
# Render Node
#===============================================================================
class RenderNode(object):

    """ Render Node in the Render Tree

    A render node will grab resources from the resource pool,
    compose or modify these resources and generate a new one.
    The new result will be put back to the resource pool to be used by
    other render nodes.

    @param name: name of the render node
    @param sources: list of name of the dependent render nodes
    """

    def __init__(self, name, source_names=list()):
        self._name = name
        self._source_names = source_names

    @property
    def name(self):
        """ name of the node """
        return self._name

    def render(self, context):
        """ render process """
#        pool = context.source_pool
#        sources = dict()
#        for name in self._source_names:
#            source = pool.get(name)
#            if not source:
#                raise MissingSource('%s can not find source %s' % \
#                                    (self._name, name))
#            sources[name] = source
#
#        result = self.__render__(context, sources)
#        pool.put(self._name, result)
#        return result
        raise NotImplementedError

    def close(self):
        pass

    def __repr__(self):
        return "%s('%s')" % (self.__class__.__name__, self._name)


#===============================================================================
# Render Tree
#===============================================================================
class RenderTree(object):

    def __init__(self, root):
        self._graph = nx.DiGraph()
        self._root = root
        self._graph.add_node(root.name, node=root)

    def add_node(self, node, parent):
        assert isinstance(node, RenderNode)
        if parent not in self._graph.nodes():
            raise UnknownParentNode(parent)
        self._graph.add_node(node.name, node=node)
        self._graph.add_edge(parent, node.name)
        return node

    def render(self, context):
        root_name = self._root.name
        for node_name in nx.dfs_postorder_nodes(self._graph, root_name):
            node = self._graph.node[node_name]['node']
            result = node.render(context)

            if node_name == root_name:
                return result
        else:
            assert False

    def close(self):
        for node_name in self._graph.nodes():
            node = self._graph.node[node_name]['node']
            node.close()

    @staticmethod
    def summary():
        pass

    @staticmethod
    def from_summary(summary):
        pass
