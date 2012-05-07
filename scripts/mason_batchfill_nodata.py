'''
Created on May 2, 2012

@author: ray
'''

import os
import sys
import subprocess


def get_raw_hgt(directory):
    for file_name in os.listdir(directory):
        if file_name.endswith('hgt'):
            file_path = os.path.join(directory, file_name)
            if os.path.isfile(file_path):
                yield file_path


def fill_nodata(src_path, dst_path):
    try:
        subprocess.check_call(['gdal_fillnodata.py',
                               '-q',
                               '-md', '100',
                               '-si', '3',
                               src_path,
                               dst_path,
                               ])
    except subprocess.CalledProcessError:
        print '%s is not valid' % src_path


def main():

    args = sys.argv
    if len(args) < 3:
        print args
        print 'Usage: fillnodata.py src_dir dst_dir'
        return

    src_dir, dst_dir = args[1], args[2]
    if src_dir == dst_dir:
        print 'Ouput Dir should be different from Source Dir'

    for hgt_data in get_raw_hgt(src_dir):

        src_path = hgt_data
        file_name, _ext = os.path.basename(src_path).split('.')
        dst_path = dst_dir + file_name

        fill_nodata(src_path, dst_path)

if __name__ == '__main__':
    main()
