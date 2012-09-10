Mason
=====

Another map tile library reinvented

Mason is a tile based map library implemented in python, which offers
a simpler way to rendering, storing and managing map tiles, including
raster images and vector data.

Similar wheels:
*  TileCache (http://tilecache.org)
*  TileStatche (http://tilestache.org)

Reinvented the wheel because we need the extra power to render even more beautiful maps.

Features
--------
* Render, storage, manage map tiles.
* Supports Mapnik2.1 as map renderer, PostGIS2.0 as raster/geometry data source.
* Uses ImageMagick as image post processing engine.
* Simple render tools.
* Built in deployable tile server

Renderers:
* Topographic map via Mapnik2
* Shaded relief map via PostGIS2.0, GDAL1.9
* Post processing using ImageMagick

Storage:
* File system
* Memcached
* MBtiles (sqlite3)

Suggested Tools
---------------
* To view or edit geographic data, try QGIS (www.qgis.org).
* PostGIS (www.postgis.org) is best way to handle large quality of geographic data.
  Note PostGIS 2.0+ is required to render raster data.
* To edit mapnik style xml, try TileMill (www.mapbox.com/tilemill).  

Dependency
----------
Python2.7+ is required, Pypy1.8 is also supported for servign static tiles only.
There is no support for python3 yet, but we will port it to py3k in the future.

Tile server using rendered tiles:
- Flask
- python-memcached (not strictly required but recommendend)

Render using mapnik
- mapnik 2.1.0 (2.0+ will work, but with limited function)
- ImageMagick
  
Render shaded relief using gdal
- GDAL 1.9 (with python binding)
  
Composite effects
- imagemagick

Install
-------
TBD...

License
-------
LGPL
