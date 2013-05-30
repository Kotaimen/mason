'''
Created on May 21, 2012

@author: ray
'''
import io
import os
import re
import subprocess

from ..utils import TempFile
from .composer import ImageComposer

try:
    output = subprocess.check_output(['convert', '-version'])
except Exception:
    raise ImportError('Convert is not found. Please Install ImageMagick.')


class CommandNotFound(Exception):
    pass


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

    def __init__(self, format):
        ImageComposer.__init__(self, format)
        self._command = None
        # Convert command string to list of arguments

    def setup_command(self, command):
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
        if not self._command:
            raise CommandNotFound
        command = list(self._command)

        files_to_delete = dict()

        for cmd_no, ref_name in self._parse_command(command):
            try:
                image_data, image_ext = image_list[ref_name]
            except KeyError:
                raise RuntimeError('Invalid tile source "%s"' % ref_name)

            # Generate a new tempfile for tiles not used yet
            if ref_name not in files_to_delete:

                # Generate a temp file name using mkstemp
                suffix = image_ext
                prefix = 'mgktle$%s-' % ref_name
                tempfile = TempFile(prefix=prefix, suffix=suffix)

                # Delete the temp file later
                files_to_delete[ref_name] = tempfile

                # Write image data to temp file
                tempfile.write(image_data)

            # Replace '%n' with real filename
            command[cmd_no] = files_to_delete[ref_name].filename

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
            for tempfile in files_to_delete.itervalues():
                tempfile.close()

    def _parse_command(self, command):

        for i in range(len(command)):
            arg = command[i]
            match = re.match(r'\{\{(\w+)\}\}', arg)
            if match:
                ref_name = match.group(1)
                yield (i, ref_name)
