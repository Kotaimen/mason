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

        if not isinstance(command, list):
            raise TileComposerError('Command should be a list of arguments')

        output_sum = 0
        for arg in command:
            if not isinstance(arg, str):
                raise TileComposerError('Argument should be string')

            match = re.match('(\w+):-', arg)
            if match:
                image_type = match.group(1)
                if image_type not in ['png', 'jpeg']:
                    raise TileComposerError('Invalid Image Type "%s"' % image_type)

                output_sum += 1
                if output_sum != 1:
                    raise TileComposerError('There should be one output!')

        self._data_type = image_type
        self._command = command

    def compose(self, tiles):
        """ Composes tiles according to the command"""

        command = self._command
        tempfiles = list()

        for idx, tile_no in self._parse_command(command):
            try:
                tile = tiles[tile_no - 1]
            except KeyError:
                TileComposerError('Tile sources & command not match.')

            data = tile.data
            ext = tile.metadata['ext']

            fd, tempname = tempfile.mkstemp(suffix='.' + ext,
                                            prefix='composer_')
            # Close the file descriptor since we are just getting a temp name
            os.close(fd)

            # Write image data to temp files
            with open(tempname, 'wb') as fp:
                fp.write(data)

            command[idx] = tempname
            tempfiles.append(tempname)

        try:
            # Execute imagemagick command
            stdout = subprocess.check_output(command)
        finally:
            # Delete temporary files
            for filename in tempfiles:
                if os.path.exists(filename):
                    os.remove(filename)

        return stdout

    def _parse_command(self, command):

        for i in range(len(command)):

            arg = command[i]
            match = re.match(r'\$(\d+)', arg)
            if match:
                tile_no = int(match.group(1))
                yield (i, tile_no)
