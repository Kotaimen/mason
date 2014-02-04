#Mason


##Another map tile library reinvented.

Mason is a tile map library implemented in python, which helps designing artisitic map themes and renendering tiles.

Similar wheels:

-  [TileCache](http://tilecache.org)
-  [TileStatche](http://tilestache.org)

Check [demos](http://maps.masonmaps.me), note its only backed by a AWS `c3.xlarge` instance.

##Features

* Renders vector/raster maps.
* Mapnik 2.2 as vector map renderer
* Postgis/GDAL as relief map renderer
* ImageMagick as post processing engine
* Simple render tools.
* Built in tile server
* Explicit buffering to overcome postgis/mapnik buffer artifiacts
* Tile storage:
	* File system
	* MBtiles
	* Tile cluster
	* S3 cluster

#Enviorment
ubuntu12.04+, MacOS Brew.

#Install
Check wiki pages.

#License
BSD
