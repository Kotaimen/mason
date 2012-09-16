""" Metadata

Created on Sep 2, 2012
@author: Kotaimen
"""

import collections


class Metadata(collections.namedtuple('_Metadata', '''tag description version
    attribution maptype''')):

    def make_dict(self):
        return self._asdict()

    @staticmethod
    def make_metadata(tag,
                      description=None,
                      version=None,
                      attribution=None,
                      maptype='basemap',
                      ):
        if description is None:
            description = ''
        if version is None:
            version = '1'
        if attribution is None:
            attribution = ''
        return Metadata(tag, description, version, attribution, maptype)

    @staticmethod
    def from_dict(mapping):
        return Metadata(**mapping)