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

        mop = McOptionParser()
        mop.configure_mop()
        (options, args) = mop.parse_args(['-d'])
        self.assertEqual(options.verbosity, 5)

        mop = McOptionParser()
        mop.configure_mop()
        (options, args) = mop.parse_args(['-vvv'])
        self.assertEqual(options.verbosity, 4)

    def test_option_onlynodes(self):
        '''Test usage of the only-nodes option'''
        mop = McOptionParser()
        mop.configure_mop()
        (options, args) = mop.parse_args(['-n', 'foo8'])
        self.assertTrue('foo8' in options.only_nodes)

        mop = McOptionParser()
        mop.configure_mop()
        (options, args) = \
            mop.parse_args(['service', 'start', '-n', 'foo1,foo2'])
        self.assertTrue(isinstance(options.only_nodes, NodeSet))
        self.assertTrue('foo1' in options.only_nodes)
        self.assertTrue('foo2' in options.only_nodes)
        self.assertTrue('service' in args and 'start' in args)

        mop = McOptionParser()
        mop.configure_mop()
        self.assertRaises(InvalidOptionError,
            mop.parse_args, ['service', 'start','-n', '[foo5]'])

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
        mop.parse_args(['service', 'start',
            '-n', 'foo[8-15]', '-x', 'foo[8-12]'])
        self.assertTrue('foo[13-15]' in options.only_nodes)
        self.assertFalse('foo[8-9]'  in options.only_nodes)
        self.assertTrue('foo[8-12]' in options.excluded_nodes)

        mop.parse_args(['service', 'start',
            '-x', 'foo[8-12]', '-n', 'foo[8-15]'])
        self.assertTrue('foo[13-15]' in options.only_nodes)
        self.assertFalse('foo[8-9]'  in options.only_nodes)
        self.assertTrue('foo[8-12]' in options.excluded_nodes)

    def test_option_version(self):
        '''Test usage of option --version'''
        mop = McOptionParser()
        mop.configure_mop()
        self.assertRaises(SystemExit, mop.parse_args, ['--version'])

    def test_option_invalid_nodeset(self):
        '''Test if nodeset/group source is invalid'''
        mop = McOptionParser()
        mop.configure_mop()
        self.assertRaises(InvalidOptionError, mop.parse_args,
                                    ['status', '-n', '@bad:group'])

        mop = McOptionParser()
        mop.configure_mop()
        self.assertRaises(InvalidOptionError, mop.parse_args,
                                    ['status', '-n', 'bad_node[set'])
