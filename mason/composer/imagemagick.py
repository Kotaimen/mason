'''
Created on May 21, 2012

@author: ray
'''
import os
import re
import tempfile
import subprocess

from ..cartographer.datatype import RenderData
from .composer import TileComposer, TileComposerError

try:
    output = subprocess.check_output(['convert', '-version'])
except Exception:
    raise ImportError('Convert is not found. Please Install ImageMagick.')


class ImageMagickError(subprocess.CalledProcessError):

    def __init__(self, returncode, cmd, output=None):
        self.returncode = returncode
        self.cmd = cmd
        self.output = output

    def __str__(self):
        return '%d\n$ %s\n%s' % (self.returncode, self.cmd, self.output)

#==============================================================================
# ImageMagick Composer
#==============================================================================


class ImageMagickComposer(TileComposer):

    """ ImageMagick Composer

    Compose tiles using ImageMagick convert command (www.imagemagick.org)

    The command is the ImageMagick convert command-line parameters, with
    following exceptions:

    - Image Source is designated as '$n', starts from 1 (eg.'$1','$2'), the
      number will be replaced with image generated from tile source list
    - Output image type is always automatic specified and is written to stdout
      as last parameter.
    - The command can be split into lines and and line starts with '#' is
      ignored.  This allows write comment in the command.

    For example, the following command::

       '''$1 -blur 0x4
          # ---Comment line ----
          $2 -compose lighten -composite'''

    Becomes::

       'convert /tmp/foo.png -blur 0x4 /tmp/bar.png -compose lighten -compose png:-'

    Note filenames is generated randomly.

    """

    def __init__(self, tag, data_type, command):
        TileComposer.__init__(self, tag, data_type)

        # Convert command string to list of arguments
        lines = ['convert -quiet -limit thread 1']
        for line in command.splitlines():
            if line.lstrip().startswith('#'):
                continue
            lines.append(line.strip())
        lines.append('%s:-' % self._data_type.name)
        self._command = ' '.join(lines).split()

    def compose(self, tiles):
        """ Composes tiles according to the command"""

        # Copy a command list since we are going to modify it in place
        command = list(self._command)

        files_to_delete = dict()

        for cmd_no, tile_no in self._parse_command(command):
            try:
                tile = tiles[tile_no - 1]
            except KeyError:
                TileComposerError('Invalid tile source "%s"' % tile_no)

            # Generate a new tempfile for tiles not used yet
            if tile_no not in files_to_delete:

                # Image extension
                ext = tile.metadata['ext']

                # Generate a temp file name using mkstemp
                fd, tempname = tempfile.mkstemp(suffix='.' + ext,
                                                prefix='mgktle$%d-' % tile_no)
                # Close the file descriptor immediately 
                # NOTE: Write using os.write() will cause fd being opened
                #       forever (even after called os.close()), and 
                #       eventually exhaust file handles, confirmed this
                #       on darwin & linux
                os.close(fd)

                # Delete the temp file later
                files_to_delete[tile_no] = tempname

                # Write image data to temp file
                with open(tempname, 'wb') as fp:
                    fp.write(tile.data)

            # Replace '%n' with real filename
            command[cmd_no] = tempname

        try:
            # Call imagemagick command
            process = subprocess.Popen(command,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            retcode = process.poll()
            if retcode:
                raise ImageMagickError(retcode, ' '.join(command),
                                       output=stderr)

            return RenderData(stdout, self._data_type)
        finally:
            # Delete temporary files
            for filename in files_to_delete.itervalues():
                if os.path.exists(filename):
                    os.remove(filename)

    def _parse_command(self, command):

        for i in range(len(command)):
            arg = command[i]
            match = re.match(r'\$(\d+)', arg)
            if match:
                tile_no = int(match.group(1))
                yield (i, tile_no)
