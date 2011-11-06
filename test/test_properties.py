#!/usr/bin/env python
import helper
import unittest
from pprint import pprint

from properties import parse_properties

def parse_properties2(fname, reps={}):
    with open(fname) as f:
        props = parse_properties(f, replace=reps)
    print('Contents of %s:' % fname)
    pprint(props)
    return props

class ParseProperties(unittest.TestCase):
    def test_parse_properties_catalina6(self):
        fname = 'examples/catalina6.properties'
        props = parse_properties2(fname)
        self.assertEqual('', props['shared.loader'])
        self.assertTrue(len(props['common.loader']) > 0)

    def test_parse_properties_catalina6_with_replacements(self):
        fname = 'examples/catalina6.properties'
        reps = {'catalina.base': 'CATALINA_BASE'}
        props = parse_properties2(fname, reps)
        self.assertEqual('CATALINA_BASE/lib', props['common.loader'][0])

    def test_parse_properties_catalina7(self):
        fname = 'examples/catalina7.properties'
        props = parse_properties2(fname)
        
unittest.TestLoader().loadTestsFromTestCase(ParseProperties)

if __name__ == "__main__":
    unittest.main()
