
from ..core import create_data_type

try:
    from .imagemagick import ImageMagickComposer
except ImportError:
    ImageMagickComposer = None


def create_tile_composer(prototype, tag, **params):
    if prototype != 'imagemagick':
        raise Exception('Composer type "%s" is not supported' % prototype)

    if not ImageMagickComposer:
        raise Exception('ImageMagic is not found.')

    # custom values
    if 'data_type' in params:
        datatype_name = params['data_type']
        del params['data_type']

        data_parameters = None
        if 'data_parameters' in params:
            data_parameters = params['data_parameters']
            del params['data_parameters']

        data_type = create_data_type(datatype_name, data_parameters)
    else:
        data_type = create_data_type('png', None)

    params['data_type'] = data_type

    return ImageMagickComposer(tag, **params)
