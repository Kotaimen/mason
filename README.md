Mason
=====

Another map tile library reinvented.

Mason is a tile map library implemented in python, which helps designing map themes 
and renendering tiles.

Check my related mapping projects for demos.

Similar wheels:
*  [TileCache](http://tilecache.org)
*  [TileStatche](http://tilestache.org)

Features
--------

Supports:
* Render, storage, manage map tiles.
* Mapnik 2.1 as map renderer, PostGIS2/GDAL as raster/geometry data source.
* ImageMagick as image post processing engine.
* Simple render tools.
* Built in tile server
* Explicit buffering to overcoming postgis/mapnik2 buffer artifiacts 

Renderers:
* Topographic map via Mapnik
* Shaded relief map via PostGIS, GDAL
* Post processing/composer using ImageMagick

Storage:
* File system
* MBtiles
* Tile Cluster

Suggested Tools
---------------
* To view or edit geographic data, try [QGIS](www.qgis.org).
* [PostGIS](www.postgis.org) is best way to handle large quality of geographic data.
  Note PostGIS 2.0+ is required to render raster data.
* To edit mapnik style xml, try [TileMill](www.mapbox.com/tilemill). 

Dependency
----------
Tested on ubuntu-12.04+ (64bit) and MacOS Lion, python 2.7+ is required.
Most GIS tools are still in python 2.x era so python3 is not supported, yet.

On ubuntu just type following to install everything:

```
apt-get -y install python-dev python-pipapt-get install imagemagick
apt-get -y install libgdal-dev python-gdal gdal-bin python-mapnik2 memcached
pip install flask networkx python-memcached
```

Note ubuntu 12.x comes with gdal 1.7 and mapnik2.0, which is outdated, you need
manually build your own version. (mapnik now comes with their own ubuntu packge, check 
[here](https://github.com/mapnik/mapnik/wiki/UbuntuInstallation) ).

On Mac with brew installed, replace `apt-get` with `brew`.


Install
-------
Just extract package to anywhere and run `./tileserver.py tests/input/world.cfg.py`.
This will start a new tile server renders a simple sketchy world map at 
`http://localhost:8080`

If you see warnings like this:
```
### LineSymbolizer properties warning: 'smooth','comp-op' are invalid,...
```
Then your mapnik is 2.0 and is outdated (and your map will *not* be sketchy), please upgrade to mapnik2.1.

License
-------
LGPL
