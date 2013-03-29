#!/usr/bin/env python

""" Dump a clustered tile storage as a geojson to check render result visually
"""

import csv
import os
import sys
import re
import geojson
from mason.core import Pyramid

def main1():
    input = sys.argv[1]
    output = sys.argv[2]
    pyramid = Pyramid(levels=range(0, 22))
    features = list()
    with open(input, 'rb') as fp:
        reader = csv.reader(fp)
        for row in reader:
            z, x, y = tuple(map(int, row))
            tile_index = pyramid.create_tile_index(z, x, y, range_check=False)
            envelope = tile_index.envelope
            coordinates = [[
                envelope.leftbottom.make_tuple(),
                envelope.lefttop.make_tuple(),
                envelope.righttop.make_tuple(),
                envelope.rightbottom.make_tuple(),
#                envelope.leftbottom.make_tuple(),
            ]]

            polygon = geojson.Polygon(coordinates=coordinates)
            feature = geojson.Feature(geometry=polygon, properties=dict(z=z, x=x, y=y))
            features.append(feature)

    collection = geojson.FeatureCollection(features=features)

    with open(output, 'wb') as fp:
        geojson.dump(collection, fp,
#                     indent=2
                     )

def main2():
    input = '/home/pset/proj/tile-export/mason/Brick/cache/export/Brick/16'
    output = 'rendered16.geojson'
    pyramid = Pyramid(levels=range(0, 22))
    features = list()
    count = 0
    for root, dirnames, filenames in os.walk(input):
        for filename in filenames:
            match = re.match(r'(\d+)-(\d+)-(\d+)@(\d+)\.zip', filename)

            if not match:
                continue

            count += 1
            if count % 100 == 0:
                print count, filename

            z, x, y, stride = tuple(map(int, (match.groups())))

            tile_index = pyramid.create_metatile_index(z, x, y, 16,)
            envelope = tile_index.envelope
            coordinates = [[
                envelope.leftbottom.make_tuple(),
                envelope.lefttop.make_tuple(),
                envelope.righttop.make_tuple(),
                envelope.rightbottom.make_tuple(),
            ]]

            polygon = geojson.Polygon(coordinates=coordinates)
            feature = geojson.Feature(geometry=polygon, properties=dict(z=z, x=x, y=y, stride=stride))
            features.append(feature)

    collection = geojson.FeatureCollection(features=features)

    with open(output, 'wb') as fp:
        geojson.dump(collection, fp,
#                     indent=2
                     )


if __name__ == '__main__':
    main1()
