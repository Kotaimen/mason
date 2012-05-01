Mason
=====

Another map tile library reinvented

Mason is a tile based map library implemented in python, which offers
a simpler way to rendering, storing and managing map tiles, including
raster images and vector data.

Similar wheels:
*  TileCache (http://tilecache.org)
*  TileStatche (http://tilestache.org)

Features
--------
* Render, storage, manage map tiles.
* Supports Mapnik2.0 as map renderer, PostGIS2.0 as raster/geometry data source.
* Uses ImageMagick as image processing engine.
* Mass render tools
* Built in deployable server

Renderers:
* Topographic map via Mapnik2
* Shaded relief map via PostGIS2.0, GDAL1.9 and ImageMagick
* GeoJson via PostGIS
* Mass-render tools

Storage:
* File system
* Memcached
* SQLite3 (mbtiles)
* Automatic sharding

Environment
-----------
Supports Python2.7, not test on Py3k, yet.  Pypy1.8 is also supported when c extension is not needed.
Note althrough Python itself is platform indpendent, most geo c-extension (geos, prj, gdal, mapnik) 
precompied on windows is 32-bit, so you won't be able to handle large data set on Windows.
Ubuntu 11.04/12.04 or MacOS Homebrew is recommonded enviorments.

Tools
-----
* To view or edit geographic data, try QGIS (www.qgis.org).
* PostGIS (www.postgis.org) is best way to handle large quality of geographic data.
  Note PostGIS 2.0+ is required to render raster data.
* To edit mapnik style xml, try TileMill (www.mapbox.com/tilemill/)


Dependency
----------
TBD...

Install
-------
TBD...

License
-------
LGPL