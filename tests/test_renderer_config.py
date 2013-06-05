'''
Created on May 31, 2013

@author: ray
'''
import unittest
from mason import renderer


class MockMetaTileIndex(object):

    @property
    def coord(self):
        return 2, 2, 3


class MockMetaTile(object):

    def __init__(self, index, data):
        self._index = index
        self._data = data

    @property
    def index(self):
        return self._index

    @property
    def data(self):
        return self._data


class MockCache(object):

    def __init__(self):
        self._cache = dict()

    def put(self, metatile):
        self._cache[metatile.index] = metatile

    def get(self, metatile_index):
        return self._cache.get(metatile_index, None)


class TestMetaTileRenderConfig(unittest.TestCase):

    def setUp(self):
        params = dict(a=1, b=2)
        self._cache = MockCache()
        self._config = renderer.MetaTileRenderConfig(
             'test',
             self._cache,
             keep_cache=True,
             **params
        )

    def tearDown(self):
        pass

    def testName(self):
        self.assertEqual(self._config.name, 'test')

    def testCache(self):
        self.assertEqual(self._config.cache, self._cache)

    def testKeepCache(self):
        self.assertTrue(self._config.keep_cache)

    def testGetParamsFromContext(self):
        metatile_index = MockMetaTileIndex()
        context = renderer.MetaTileContext(metatile_index)
        self.assertDictEqual(self._config.get_params_from_context(context),
                             dict(a=1, b=2))


class TestHillShadingNodeConfig(unittest.TestCase):

    def testDefault(self):
        config = renderer.HillShadingNodeConfig('test')

        metatile_index = MockMetaTileIndex()
        context = renderer.MetaTileContext(metatile_index)
        params = config.get_params_from_context(context)
        self.assertDictEqual(params, dict(zfactor=1,
                                          scale=1,
                                          altitude=45,
                                          azimuth=315))

    def testGetParamsFromContext(self):
        config = renderer.HillShadingNodeConfig('test',
                                                zfactor=[1, 2, 3],
                                                scale=[1, 2, 3],
                                                altitude=[1, 2, 3],
                                                azimuth=[1, 2, 3]
                                                )

        metatile_index = MockMetaTileIndex()
        context = renderer.MetaTileContext(metatile_index)
        params = config.get_params_from_context(context)
        self.assertDictEqual(params, dict(zfactor=3,
                                          scale=3,
                                          altitude=3,
                                          azimuth=3))


class TestHomeBrewHillShadingNodeConfig(unittest.TestCase):

    def testDefault(self):
        self.assertRaises(renderer.ParamNotFound,
                          renderer.HomeBrewHillShadingNodeConfig, 'test')

    def testGetParamsFromContext(self):

        config = renderer.HomeBrewHillShadingNodeConfig(
            'test',
            dataset_path=['/1', '/2', '/3'],
            zfactor=[1, 2, 3],
            scale=[1, 2, 3],
            altitude=[1, 2, 3],
            azimuth=[1, 2, 3]
        )

        metatile_index = MockMetaTileIndex()
        context = renderer.MetaTileContext(metatile_index)
        params = config.get_params_from_context(context)
        self.assertDictEqual(params, dict(prototype='shaderelief',
                                          dataset_path='/3',
                                          zfactor=3,
                                          scale=3,
                                          altitude=3,
                                          azimuth=3))


class TestColorReliefNodeConfig(unittest.TestCase):

    def testDefault(self):
        self.assertRaises(renderer.ParamNotFound,
                          renderer.ColorReliefNodeConfig, 'test')

    def testGetParamsFromContext(self):
        config = renderer.ColorReliefNodeConfig(
            'test',
            color_context='/color_context.txt'
        )

        metatile_index = MockMetaTileIndex()
        context = renderer.MetaTileContext(metatile_index)
        params = config.get_params_from_context(context)
        self.assertDictEqual(params, dict(color_context='/color_context.txt'))


class TestStorageNodeConfig(unittest.TestCase):

    def testDefault(self):
        self.assertRaises(renderer.ParamNotFound,
                          renderer.StorageNodeConfig, 'test')

    def testGetParamsFromContext(self):
        config = renderer.StorageNodeConfig(
            'test',
            storage=dict(prototype='metacache', root='/')
        )

        metatile_index = MockMetaTileIndex()
        context = renderer.MetaTileContext(metatile_index)
        params = config.get_params_from_context(context)
        self.assertDictEqual(params,
                             dict(storage=dict(prototype='metacache', root='/'),
                                  default=None)
                             )


class TestMapnikNodeConfig(unittest.TestCase):

    def testDefault(self):
        self.assertRaises(renderer.ParamNotFound,
                          renderer.MapnikNodeConfig, 'test')

    def testGetParamsFromContext(self):
        config = renderer.MapnikNodeConfig(
            'test',
            theme='/theme.xml',
        )

        metatile_index = MockMetaTileIndex()
        context = renderer.MetaTileContext(metatile_index)
        params = config.get_params_from_context(context)
        self.assertDictEqual(params,
                             dict(theme='/theme.xml',
                                  projection='EPSG:3857',
                                  prototype='mapnik',
                                  image_type='png',
                                  image_parameters=None,
                                  scale_factor=1.0,
                                  force_reload=False,
                                  buffer_size=0,
                                  )
                             )


class TestRasterRenderConfig(unittest.TestCase):

    def testDefault(self):
        self.assertRaises(renderer.ParamNotFound,
                          renderer.RasterNodeConfig, 'test')

    def testGetParamsFromContext(self):
        config = renderer.RasterNodeConfig(
            'test',
            dataset_path=['/1', '/2', '/3'],
        )

        metatile_index = MockMetaTileIndex()
        context = renderer.MetaTileContext(metatile_index)
        params = config.get_params_from_context(context)
        self.assertDictEqual(params,
                             dict(dataset_path='/3',
                                  prototype='dataset',
                                  resample_method=None,
                                  target_nodata= -32768,
                                  target_projection='EPSG:3857',
                                  work_memory=1024
                                  )
                             )


class TestImageMagicComposerNodeConfig(unittest.TestCase):

    def testDefaut(self):
        self.assertRaises(renderer.ParamNotFound,
                          renderer.ImageMagicComposerNodeConfig, 'test')

    def testGetParamsFromContext(self):
        config = renderer.ImageMagicComposerNodeConfig(
            'test',
            command='$1',
            command_parameter=None,
            format='png'
        )

        metatile_index = MockMetaTileIndex()
        context = renderer.MetaTileContext(metatile_index)
        params = config.get_params_from_context(context)
        self.assertDictEqual(params,
                             dict(command='$1',
                                  format='png',
                                  necessary_nodes=[]
                                  )
                             )

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
