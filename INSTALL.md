
#Install

Like all cartography applications, Mason integrated a lot of different tools thus have a very large dependency tree.
Here is a step by step installation guide on ubuntu 12.04-x64 versoin (also works on 12.10 and later).

On MacOS, replace `apt-get install` with `brew install`, `apt-get install python-xxxx` with `pip install`.

## First, install build tools:

```
sudo apt-get install python-dev g++ make swig git python-pip
```

## PROJ.4

Install from package manager:

```
apt-get install libproj-dev
```

Or build it from source.

Check latest version from [here](http://trac.osgeo.org/proj/):

```
wget http://download.osgeo.org/proj/proj-4.8.0.tar.gz
cd proj-4.8.0
./configure && make 
sudo make install
```

## GEOS

Install from package manager:

```
apt-get install libgeos-dev
```

Or build it from source (recommended).

Check latest version from [here](http://trac.osgeo.org/geos/):

```
wget http://download.osgeo.org/geos/geos-3.4.2.tar.bz2
tar xf geos-3.4.2.tar.bz2
cd geos-3.4.2
./configure --enable-python && make 
sudo make install
```

## GDAL

Mason requires gdal 1.9.0+ for DEM processing, and scipy-gdal for custom high quality hill shading.

So you have to compile GDAL 
But apt-get comes with v1.7.0 without numpy/scipy binding so you’ll have to compile and install it from source.

Note: this will probably have some issue with your existing applications which uses default libgdal-dev, eg: QGIS.

Check latest version [here](http://trac.osgeo.org/gdal/wiki/DownloadSource).  

Install scipy/numpy first otherwise gdal won't compile scipy python binding.

```
sudo apt-get install python-scipy python-numpy
```

Then download gdal source and build and install it.
Gdal make takes sometime so `make -j CORE_NUM` helps.

```
http://download.osgeo.org/gdal/1.10.1/gdal-1.10.1.tar.gz
tar xf gdal-1.10.1.tar.gz
cd gdal-1.10.1
./configure --with-python
make
sudo make install
```

##Mapnik
Mapnik is required for vector to raster rendering.

Mapnik comes with their own ubuntu packge, check
[here](https://github.com/mapnik/mapnik/wiki/UbuntuInstallation).

For manually build, you need install following libraries first:

```
sudo apt-get inpng-dev libxml2-dev libboost1.48-all-dev libicu-dev libfreetype6-dev libsqlite3-dev libpq-dev
```

Mapnik requires boost1.47+.
Note on MacOS, you must build your own boost library instead of the default bottle version.

Compile and install mapnik:
 
```
wget http://mapnik.s3.amazonaws.com/dist/v2.2.0/mapnik-v2.2.0.tar.bz2
tar xf mapnik-v2.2.0.tar.bz2 
cd mapnik-v2.2.0
./scons/scons.py configure
./scons/scons.py --jobs=CPU_NUM
sudo ./scons/scons.py install
```

Mapnik compile takes a lot of time (and memory) so be patient!
(Took 17m on my 2013 MBP using 4 cores & 8G memory).

##ImageMagick
Imagemagick is required for advanced image processing and layer compositing.  Usually the version come with the package manager is fine, however be aware different imagemagick ususally produce slightly different results.

```
sudo apt-get install imagemagick
```

Note: 
There is a bug in ubuntu 13.10's imagemagick which causes some composer configuration fail:

```
convert: magick/cache-view.c:477: GetCacheViewAuthenticPixels: Assertion `id < (int) cache_view->number_threads' failed.
```

Workaround (instead of compiling your own imagemagick) is disable OpenMP support, this won't affect render performance since Mason disables multithreading in ImageMagick anyway:

```
export OMP_THREAD_LIMIT=1
```

##Support Libraries
For memcache tile storage you obviously need memcache and its python binding:

```
sudo apt-get install memcached python-memcache
```

For Python image processing you need PIL:

```
sudo apt-get install python-imaging
```

For AWS S3 tile storage you need boto, this should be installed via PIP since package version is usually outdated.

```
sudo pip install boto
```

Finally, flask framework:

```
sudo pip install flask
```

#Test

Clone mason code then:

```
cd mason
export PYTHONPATH=`pwd`
python test
```
Note: S3 related tests won't pass unless you modified default test bucketname and provided proper boto access_key.
