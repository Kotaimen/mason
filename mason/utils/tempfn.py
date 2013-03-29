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

# XXX: Disable this check so we don't call os.stat twice...
#    if not os.path.exists(dir):
#        raise IOError(errno.EEXIST, "Folder %s does not exist." % dir)

    names = tempfile._get_candidate_names()
    for _seq in xrange(tempfile.TMP_MAX):
        name = names.next()
        filename = os.path.join(dir, prefix + name + suffix)
        if not os.path.exists(filename):
            return filename

    raise IOError(errno.EEXIST, "No usable temporary filename found")


class TempFile(object):

    def __init__(self, prefix='', suffix=str(os.getpid())):
        """ create a temporary raster file """
        self._filename = create_temp_filename(suffix, prefix)

    @property
    def filename(self):
        """ return temporary filename """
        return self._filename

    def read(self):
        """ load data from file """
        with open(self._filename, 'rb') as fp:
            return fp.read()

    def write(self, data):
        """ save data to file"""
        with open(self._filename, 'wb') as fp:
            fp.write(data)

    def close(self):
        if os.path.exists(self._filename):
            os.remove(self._filename)
