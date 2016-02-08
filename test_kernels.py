#!/usr/bin/env python3

"""
This reads multiple kernel test cases from YAML file(s), generates the unittest
objects for each, and then runs the unittest(s).

The yaml file is expected to contain one or more documents like, which
correspond to the equivalent named fields in KernelTest

    kernel_name: foo
    language_name: bar
    code_hello_world: print
    completion_samples:
        - text: foo
          matches:
            - fooo
            - foooo
        - text: bar
          matches:
            - barrr
    complete_code_samples:
     - foo
     - bar
    incomplete_code_samples:
     - foo
     - bar
    invalid_code_samples:
     - foo
     - bar
    code_page_something: foo
"""

import yaml
import unittest
import jupyter_kernel_test as jkt
import argparse
import os

def load_specs(specfile):
    """
    Load a YAML file, and convert each of the documents within into a
    KernelTests subclass. Returns a list of class objects.
    """
    test_classes = []
    assert os.path.exists(specfile)
    with open(specfile) as sf:
        for spec in yaml.load_all(sf):
            assert isinstance(spec, dict)
            assert 'kernel_name' in spec
            tc = type(spec['kernel_name'], (jkt.KernelTests, ), spec)
            test_classes.append(tc)
    return test_classes

def generate_test_suite(testclasses):
    "Generate a TestSuite class from a list of unittest classes."
    tests = []
    for testclass in testclasses:
        tests.append(unittest.TestLoader().loadTestsFromTestCase(testclass))
    return unittest.TestSuite(tests)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("specfiles", nargs="+",
                        help="YAML files containing test specs")
    parser.add_argument("-v", "--verbosity", default=2, type=int,
                        help="unittest verbosity")
    opts = parser.parse_args()

    for f in opts.specfiles:
        suite = generate_test_suite(load_specs(f))
        unittest.TextTestRunner(verbosity=opts.verbosity).run(suite)
