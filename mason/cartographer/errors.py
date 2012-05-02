'''
Created on May 2, 2012

@author: ray
'''

#===============================================================================
# Errors
#===============================================================================
class CartographerError(Exception):
    pass


#===============================================================================
# Mapnik Errors 
#===============================================================================
class MapnikError(CartographerError):
    pass

class MapnikVersionError(MapnikError):
    pass

class MapnikThemeNotFound(MapnikError):
    pass

class MapnikTypeError(MapnikError):
    pass

#===============================================================================
# GDAL Errors
#===============================================================================
class GDALError(CartographerError):
    pass

class GDALTypeError(GDALError):
    pass
