""" Metadata

Created on Sep 2, 2012
@author: Kotaimen
"""

import collections


class Metadata(collections.namedtuple('_Metadata', '''tag description version
    attribution maptype dispname ''')):

    def make_dict(self):
        return self._asdict()

    @staticmethod
    def make_metadata(tag,
                      description=None,
                      version=None,
                      attribution=None,
                      maptype='basemap',
                      dispname=None,
                      ):
        if description is None:
            description = ''
        if version is None:
            version = '1'
        if attribution is None:
            attribution = ''
        assert maptype in ['basemap', 'overlay']
        if dispname is None:
            dispname = tag
        return Metadata(tag, description, version, attribution, 
                        maptype, dispname)

    @staticmethod
    def from_dict(mapping):
        mapping = dict(mapping)
        tag = mapping['tag']
        if not isinstance(tag, str):
            mapping['tag'] = str(tag)
        return Metadata(**mapping)
