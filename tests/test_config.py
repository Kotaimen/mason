# -*- coding:utf-8 -*-
'''
Created on Sep 13, 2012

@author: ray
'''
import unittest
from mason.config import RenderConfigParser


class ConfigurationTest(unittest.TestCase):

    def testParse(self):
        configure_parser = RenderConfigParser()

        test_config = './input/test_config.cfg.py'
        render_root = configure_parser.parse(test_config)
        renderer = render_root.renderer


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
