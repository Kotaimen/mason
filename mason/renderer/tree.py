# -*- coding:utf-8 -*-
'''
Base class of MetaTile renderer

Created on March 14, 2013
@author: ray
'''

import collections

#===============================================================================
# Context
#===============================================================================
class RenderContext(object):
    pass


#===============================================================================
# Render Node
#===============================================================================
class RenderNode(object):

    """ Render Node in the Render Tree

    @param name: name of the render node
    """

    def __init__(self, name):
        self._name = name
        self._children = collections.OrderedDict()

    @property
    def name(self):
        """ name of the node """
        return self._name

    def add_child(self, child):
        """ append a child """
        self._children[child.name] = child

    def render(self, context):
        """ render process """
        sources = collections.OrderedDict()
        for name, child in self._children.items():
            sources[name] = child.render(context)

#        print 'Rendering %s: %s' % (self._name, repr(context))
        result = self._render_imp(context, sources)
        return result

    def close(self):
        pass

    def _render_imp(self, context, sources):
        raise NotImplementedError

    def __repr__(self):
        return "%s('%s')" % (self.__class__.__name__, self._name)
