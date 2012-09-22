Mason
=====

Another map tile library reinvented.

Mason is a tile map library implemented in python, which helps designing map themes 
and renendering tiles.
Check samples at Mapbox: http://tiles.mapbox.com/kotaimen.

Similar wheels:
*  TileCache (http://tilecache.org)
*  TileStatche (http://tilestache.org)

Version 0.9.0

Features
--------

Feature:
* Render, storage, manage map tiles.
* Mapnik2.1 as map renderer, PostGIS2.0 as raster/geometry data source.
* ImageMagick as image post processing engine.
* Simple render tools.
* Built in tile server
* Explicit buffering to overcoming postgis/mapnik2 buffer artifiacts 

Renderers:
* Topographic map via Mapnik2
* Shaded relief map via PostGIS2.0, GDAL1.9
* Post processing/composer using ImageMagick

Storage:
* File system
* MBtiles (sqlite3)

Suggested Tools
---------------
* To view or edit geographic data, try QGIS (www.qgis.org).
* PostGIS (www.postgis.org) is best way to handle large quality of geographic data.
  Note PostGIS 2.0+ is required to render raster data.
* To edit mapnik style xml, try TileMill (www.mapbox.com/tilemill).  

Dependency
----------
Python2.7+ is required (no support for python3 yet)

- Flask
- python-memcached (not strictly required but recommendend)
- mapnik 2.1.0 (2.0+ will work, but with limited function)
- ImageMagick
- GDAL 1.9 (with python binding)
- imagemagick

Install
-------
Just extract package to anywhere and run `./tileserver.py tests/input.world.cfg.py`.
This will start a new tile server renders a simple sketchy world map at 
http://localhost:8080

License
-------
LGPL
