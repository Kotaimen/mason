Mason
=====

Another map tile library reinvented

Mason is a tile based map library implemented in python, which offers
a simpler way to rendering, storing and managing map tiles, including
raster images and vector data.

Similar wheels:
*  TileCache (http://tilecache.org)
*  TileStatche (http://tilestache.org)

Reinvented the wheel because we need the extra power to render eveb more beautiful maps.

Version 0.8.0

Features
--------
* Render, storage, manage map tiles.
* Supports Mapnik2.0 as map renderer, PostGIS2.0 as raster/geometry data source.
* Uses ImageMagick as image post processing engine.
* Simple but efficient mass render tools.
* Built in deployable tile server

Renderers:
* Topographic map via Mapnik2
* Shaded relief map via PostGIS2.0, GDAL1.9
* Post processing using ImageMagick

Storage:
* File system
* Memcached
* MBtiles (sqlite3)

Environment
-----------
Supports Python2.7, not test on Py3k, yet.  Pypy1.8 is also supported when c extension is not needed.
Note althrough Python itself is platform indpendent, most geo c-extension (geos, prj, gdal, mapnik) 
precompied on windows is 32-bit, so you won't be able to handle large data set on Windows.
Tested on Ubuntu 11.04+ and OSX Homebrew.

Suggested Tools
---------------
* To view or edit geographic data, try QGIS (www.qgis.org).
* PostGIS (www.postgis.org) is best way to handle large quality of geographic data.
  Note PostGIS 2.0+ is required to render raster data.
* To edit mapnik style xml, try TileMill (www.mapbox.com/tilemill).  
  Note: at the time of writing, TileMill (0.9.1) is *not* stable, and has performance problem 
  when host has lots of cores (write lock hunger on sqlite) use supplied tilerenderer.py instead.

Dependency
----------
Python2.7+ is required, Pypy1.8 is also supported for servign static tiles only.
There is no support for python3 yet, but we will port it to py3k in the future.

Tile server using rendered tiles:
- cherrypy
- python-memcached (not strictly required but recommendend)

Render using mapnik
- mapnik 2.0.0+ (and all mapnik dependencies, see mapnik install manual)
- pil (any recent version will work) or imagemagick
  
Render shaded relief using gdal
- gdal 1.9
  
Composite effects
- imagemagick

Install
-------
TBD...

License
-------
LGPL
