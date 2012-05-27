

try:
    from .imagemagick import ImageMagickComposer
except ImportError:
    ImageMagickComposer = None


def create_tile_composer(prototype, tag, data_type, **param):
    if not ImageMagickComposer:
        raise Exception('ImageMagic is not found.')

    return ImageMagickComposer(tag, data_type, **param)
