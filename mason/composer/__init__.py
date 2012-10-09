# -*- coding:utf-8 -*-

try:
    from .imagemagick import ImageMagickComposer
except ImportError:
    ImageMagickComposer = None
