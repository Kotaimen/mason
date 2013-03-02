# -*- coding:utf-8 -*-
'''
Created on Aug 30, 2012

@author: ray
'''
import os
import errno
import tempfile


def create_temp_filename(suffix='', prefix='tmp', dir=None):
    """ Create a temporary file name with specified suffix and prefix.
        System temp folder will be used if folder is None.
    """
    assert isinstance(suffix, basestring)
    assert isinstance(prefix, basestring)

    if not dir:
        dir = tempfile.gettempdir()

    if not os.path.exists(dir):
        raise IOError(errno.EEXIST, "Folder %s does not exist." % dir)

    names = tempfile._get_candidate_names()
    for _seq in xrange(tempfile.TMP_MAX):
        name = names.next()
        filename = os.path.join(dir, prefix + name + suffix)
        if not os.path.exists(filename):
            return filename

    raise IOError(errno.EEXIST, "No usable temporary filename found")
