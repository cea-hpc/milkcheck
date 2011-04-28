# coding=utf-8
# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This is the entry point of the program.
"""

import sys
sys.path.insert(0,"/cea/home/gpocre/tatibouetj/internship/prod/code/tests")
sys.path.insert(1,"/cea/home/gpocre/tatibouetj/internship/prod/code/lib")

from unittest import TestLoader, TextTestRunner
from MilkCheckTests.EngineTests.ServiceTest import ActionTest
from MilkCheckTests.EngineTests.ServiceTest import ServiceTest
from MilkCheckTests.EngineTests.BaseServiceTest import BaseServiceTest

if __name__ == "__main__":

    # dict of test_suite
    tests_suites = {}
    
    # Load test classes
    loader = TestLoader()
    tests_suites["Action"] = loader.loadTestsFromTestCase(ActionTest)
    tests_suites["Service"] = loader.loadTestsFromTestCase(ServiceTest)
    tests_suites["BService"] = loader.loadTestsFromTestCase(BaseServiceTest)
    
    runner = TextTestRunner(verbosity=2)
    
    for name in tests_suites:
        print "============== %s test suite ==============" % name
        runner.run(tests_suites[name])