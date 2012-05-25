'''
Created on May 21, 2012

@author: ray
'''
import os
import re
import tempfile
import subprocess

from .composer import TileComposer, TileComposerError

try:
    output = subprocess.check_output(['convert', '-version'])
except Exception:
    raise ImportError('Convert is not found. Please Install ImageMagick.')


#==============================================================================
# ImageMagick Composer
#==============================================================================
class ImageMagickComposer(TileComposer):

    """ ImageMagick Composer

    Compose tiles with ImageMagick tools according to the
    specified command.

    Image Source is designated as '$n', n starts from 1,
    eg.'$1','$2'.

    Image output should not be specified, since that will
    be deduced from the image_type by the composer.

    Samples:
        command = 'convert $1 $2 -compose lighten -composite'

    the number of source corresponds with the order of the
    tiles passed into the compose method, which is also the order
    of the sources defined in the composer source.

    """

    def __init__(self, tag, command):
        TileComposer.__init__(self, tag)

        # output image should be sent to stdout(use '-')
        match = re.search('(\w+):-', command)
        if not match:
            raise TileComposerError('Output Image Type is missing.')

        # get image type from imagemagick command
        image_type = match.group(1)
        if image_type not in ['png', 'jpeg']:
            raise TileComposerError('Invalid Image Type "%s"' % image_type)

        self._data_type = image_type
        self._command = command

    def compose(self, tiles):
        """ Composes tiles according to the command"""

        temp_files = list()

        # Generate proper temp file for imagemagick (it don't accept
        # images from stdin)
        def sourcerepl(match):
            try:
                tile = tiles[int(match.group(1)) - 1]
            except KeyError:
                TileComposerError('Tile sources and command does not match.')

            data = tile.data
            ext = tile.metadata['ext']

            fd, tempname = tempfile.mkstemp(suffix='.' + ext,
                                            prefix='composer_')
            # Close the file descriptor since we are just getting a temp name
            os.close(fd)
            # Write image data to temp files
            with open(tempname, 'wb') as fp:
                fp.write(data)
            temp_files.append(tempname)
            return tempname

        try:
            # Execute imagemagick command
            command = re.sub(r'\$(\d+)', sourcerepl, self._command).split()
            stdout = subprocess.check_output(command)
        finally:
            # Delete temporary files
            for filename in temp_files:
                if os.path.exists(filename):
                    os.remove(filename)

        return stdout
