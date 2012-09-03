'''
Created on Sep 2, 2012

@author: Kotaimen
'''


class Metadata(dict):

    def __init__(self,
                 tag,
                 description=None,
                 version=None,
                 attribution=None,
                 ):
        if description is None:
            description = ''
        if version is None:
            version = '1'
        if attribution is None:
            attribution = ''
        self.tag = tag
        self.description = description
        self.version = version
        self.attribution = attribution

    def summarize(self):
        return dict(tag=self.tag,
                    description=self.dscription,
                    version=self.version,
                    attribution=self.attribution)

    @staticmethod
    def from_dict(mapping):
        return Metadata(**mapping)
