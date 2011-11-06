#!/usr/bin/env python
import helper
import unittest

from pprint import pprint
from ear import Ear

example_ear = 'examples/mvn-example/example-ear/target/example-ear-1.0.ear'

class ParseApplicationDescriptor(unittest.TestCase):
    def test_Ear(self):
        e = Ear(example_ear)
        print("Modules: %s" % e.modules)
        print("Libraries: %s" % e.libraries)
        
unittest.TestLoader().loadTestsFromTestCase(ParseApplicationDescriptor)

if __name__ == "__main__":
    unittest.main()
