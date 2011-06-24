# Copyright CEA (2011)
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

from os import environ
from os.path import abspath
from unittest import TestCase
from MilkCheck.Config.Configuration import SyntaxChecker

class SyntaxCheckerTest(TestCase):
    '''Test cases for the class SyntaxChecker'''

    def test_instanciation(self):
       '''Test creation of a SyntaxChecker object'''
       self.assertTrue(SyntaxChecker())
       self.assertRaises(SystemExit, SyntaxChecker,
            file_rules_path='test/fake.yaml')
       self.assertRaises(SystemExit, SyntaxChecker,
            file_rules_path='%s/%s'\
            %(environ['PYTHONPATH'],
            '../tests/MilkCheckTests/ConfigTests/%s'
            % 'CheckingTestFiles/checking1.yaml'))
       self.assertRaises(SystemExit, SyntaxChecker,
            file_rules_path='%s/%s'\
            %(environ['PYTHONPATH'],
            '../tests/MilkCheckTests/ConfigTests/%s'
            % 'CheckingTestFiles/checking2.yaml'))

    def test_compile_regex(self):
        '''Test compilation regex from checking file'''
        scheck = SyntaxChecker(
        file_rules_path='%s/%s'\
        %(environ['PYTHONPATH'],
        '../tests/MilkCheckTests/ConfigTests/%s'
        % 'CheckingTestFiles/checking3.yaml'))
        self.assertEqual(len(scheck._rules), 5)
        scheck = SyntaxChecker(
        file_rules_path='%s/%s'\
        %(environ['PYTHONPATH'],
        '../tests/MilkCheckTests/ConfigTests/%s'
        % 'CheckingTestFiles/checking4.yaml'))
        self.assertEqual

    def test_validate(self):
        '''Test the validation of the document'''
        scheck = SyntaxChecker()
        dty = '../tests/MilkCheckTests/ConfigTests/YamlTestFiles/sample_1/'
        fi = 'sample_1.yaml'
        scheck.validate('%s%s' % (dty, fi))