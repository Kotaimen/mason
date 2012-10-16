# -*- coding:utf-8 -*-
'''
Created on Sep 13, 2012

@author: ray
'''
import unittest
from mason.config import RenderConfigParser, RenderTree


class ConfigurationTest(unittest.TestCase):

    def testParse(self):
        config = RenderConfigParser()
        config.read('./input/test_config.cfg.py')

        p = RenderTree(config)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
