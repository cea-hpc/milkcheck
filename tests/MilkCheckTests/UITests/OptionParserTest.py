# Copyright CEA (2011)
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This modules defines the tests cases targeting the class MilkCheckOptionParser
"""

# Classes
from unittest import TestCase
from ClusterShell.NodeSet import NodeSet, NodeSetException
from MilkCheck.UI.OptionParser import McOptionParser, InvalidOptionError

class McOptionParserTest(TestCase):

    def test_instanciation(self):
        '''Test creation of an McOptionParser'''
        self.assertTrue(McOptionParser())

    def test_debug_config(self):
        '''Test configuration of the debug mode'''
        mop = McOptionParser()
        mop.configure_mop()
        (options, args) = mop.parse_args(['-d'])
        self.assertEqual(options.verbosity, 5)
        self.assertTrue(options.debug)

        mop = McOptionParser()
        mop.configure_mop()
        (options, args) = mop.parse_args(['-d'])
        self.assertEqual(options.verbosity, 5)
        self.assertTrue(options.debug)

        mop = McOptionParser()
        mop.configure_mop()
        (options, args) = mop.parse_args(['-vvv'])
        self.assertEqual(options.verbosity, 4)
        self.assertFalse(options.debug)

    def test_option_onlynodes(self):
        '''Test usage of the only-nodes option'''
        mop = McOptionParser()
        mop.configure_mop()
        (options, args) = mop.parse_args(['-n', 'fortoy8'])
        self.assertTrue('fortoy8' in options.only_nodes)

        mop = McOptionParser()
        mop.configure_mop()
        (options, args) = \
            mop.parse_args(['robinhood', 'start', '-n', 'fortoy1,fortoy2'])
        self.assertTrue(isinstance(options.only_nodes, NodeSet))
        self.assertTrue('fortoy1' in options.only_nodes)
        self.assertTrue('fortoy2' in options.only_nodes)
        self.assertTrue('robinhood' in args and 'start' in args)

        mop = McOptionParser()
        mop.configure_mop()
        self.assertRaises(InvalidOptionError,
            mop.parse_args, ['robinhood', 'start','-n', '[fortoy5]'])

    def test_option_configdir(self):
        '''Test usage of the configdir option'''
        mop = McOptionParser()
        mop.configure_mop()
        (options, args) = \
            mop.parse_args(['-c', '/usr/bin'])
        self.assertEqual(options.config_dir, '/usr/bin')

        mop = McOptionParser()
        mop.configure_mop()
        self.assertRaises(InvalidOptionError,
            mop.parse_args, ['-c', '/duke/'])

    def test_option_excluded_nodes(self):
        '''Test usage of the excluded_nodes option'''
        mop = McOptionParser()
        mop.configure_mop()
        (options, args) = \
        mop.parse_args(['robinhood', 'start',
            '-n', 'fortoy[8-15]', '-x', 'fortoy[8-12]'])
        self.assertTrue('fortoy[13-15]' in options.only_nodes)
        self.assertFalse('fortoy[8-9]'  in options.only_nodes)
        self.assertTrue('fortoy[8-12]' in options.excluded_nodes)

    def test_option_version(self):
        '''Test usage of option --version'''
        mop = McOptionParser()
        mop.configure_mop()
        (options, args) = mop.parse_args(['--version'])
        self.assertTrue(options.version)
