'''
Created on May 21, 2012

@author: ray
'''
import io
import os
import re
import subprocess

from ..utils import create_temp_filename
from .composer import ImageComposer

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


class ImageMagickComposer(ImageComposer):

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

    def __init__(self, format, command):
        ImageComposer.__init__(self, format)

        # Convert command string to list of arguments
        lines = ['convert -quiet -limit thread 1']
        for line in command.splitlines():
            if line.lstrip().startswith('#'):
                continue
            lines.append(line.strip())
        lines.append('%s:-' % self._format)
        self._command = ' '.join(lines).split()

    def compose(self, image_list):
        """ Composes tiles according to the command"""

        # Copy a command list since we are going to modify it in place
        command = list(self._command)

        files_to_delete = dict()

        for cmd_no, tile_no in self._parse_command(command):
            try:
                image_data, image_ext = image_list[tile_no - 1]
            except KeyError:
                raise RuntimeError('Invalid tile source "%s"' % tile_no)

            # Generate a new tempfile for tiles not used yet
            if tile_no not in files_to_delete:

                # Generate a temp file name using mkstemp
                suffix = image_ext
                prefix = 'mgktle$%d-' % tile_no
                tempname = create_temp_filename(suffix=suffix, prefix=prefix)

                # Delete the temp file later
                files_to_delete[tile_no] = tempname

                # Write image data to temp file
                with open(tempname, 'wb') as fp:
                    fp.write(image_data)

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

            return io.BytesIO(stdout)
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
