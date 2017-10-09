# Copyright CEA (2011-2017)
# Contributor: TATIBOUET Jeremie

"""
This modules defines the tests cases targeting the class MilkCheckOptionParser
"""

import os
import tempfile
import unittest

from ClusterShell.NodeSet import NodeSet

from MilkCheck.UI.OptionParser import McOptionParser, InvalidOptionError

class McOptionParserTest(unittest.TestCase):

    def setUp(self):
        self.mop = McOptionParser()
        self.mop.configure_mop()

    def test_debug_config(self):
        """Test configuration of the debug mode"""
        options, _ = self.mop.parse_args(['-d'])
        self.assertEqual(options.verbosity, 5)

    def test_verbose(self):
        """Test configuration of the verbose mode"""
        options, _ = self.mop.parse_args(['-vvv'])
        self.assertEqual(options.verbosity, 4)

    def test_option_onlynodes_simple(self):
        """Test simple usage of the only-nodes option"""
        options, _ = self.mop.parse_args(['-n', 'foo8'])
        self.assertEqual('foo8', str(options.only_nodes))

    def test_option_onlynodes_ns(self):
        """Test nodeset usage of the only-nodes option"""
        options, args = self.mop.parse_args(['service', 'start',
                                             '-n', 'foo1,foo2'])
        self.assertTrue(isinstance(options.only_nodes, NodeSet))
        self.assertTrue('foo1' in options.only_nodes)
        self.assertTrue('foo2' in options.only_nodes)
        self.assertTrue('service' in args and 'start' in args)

    def test_option_configdir(self):
        """Test usage of the configdir option"""
        tmpdir = tempfile.mkdtemp()
        try:
            options, _ = self.mop.parse_args(['-c', tmpdir])
        finally:
            os.rmdir(tmpdir)
        self.assertEqual(options.config_dir, tmpdir)

    def test_configdir_missing_dir(self):
        """-c with a non-existent directory raises an error"""
        self.assertFalse(os.path.exists('/foobar'))
        self.assertRaises(InvalidOptionError, self.mop.parse_args,
                          ['-c', '/foobar'])

    def test_option_excluded_nodes(self):
        """Test usage of the excluded_nodes option"""
        options, _ = self.mop.parse_args(['service', 'start',
                                          '-n', 'foo[8-15]', '-x', 'foo[8-12]'])
        self.assertTrue('foo[13-15]' in options.only_nodes)
        self.assertFalse('foo[8-9]' in options.only_nodes)
        self.assertTrue('foo[8-12]' in options.excluded_nodes)

        options, _ = self.mop.parse_args(['service', 'start', '-x', 'foo[8-12]',
                                          '-n', 'foo[8-15]'])
        self.assertTrue('foo[13-15]' in options.only_nodes)
        self.assertFalse('foo[8-9]' in options.only_nodes)
        self.assertTrue('foo[8-12]' in options.excluded_nodes)

    def test_option_version(self):
        """Test usage of option --version"""
        self.assertRaises(SystemExit, self.mop.parse_args, ['--version'])

    def test_option_invalid_nodeset(self):
        """Test if nodeset/group source is invalid"""
        self.assertRaises(InvalidOptionError, self.mop.parse_args,
                          ['status', '-n', '@bad:group'])

    def test_option_bad_nodeset_syntax(self):
        """Test if nodeset syntax is valid"""
        self.assertRaises(InvalidOptionError, self.mop.parse_args,
                          ['status', '-n', 'bad_node[set'])

    def test_option_tags(self):
        """Test --tags option"""
        options, _ = self.mop.parse_args(['-t', 'tag1'])
        self.assertEqual(options.tags, set(['tag1']))

        options, _ = self.mop.parse_args(['-t', 'tag1,tag2', '-t', 'tag3'])
        self.assertEqual(options.tags, set(['tag1', 'tag2', 'tag3']))

    def test_option_report_full(self):
        """Check report configuration option"""
        options, _ = self.mop.parse_args(['--report=full'])
        self.assertEqual(options.report, 'full')

    def test_option_report_invalid(self):
        """invalid report type raises an error"""
        self.assertRaises(InvalidOptionError, self.mop.parse_args,
                          ['--report=xxxx'])

    def test_option_summary_translation(self):
        """Check summary translation"""
        options, _ = self.mop.parse_args(['-s'])
        self.assertEqual(options.report, 'default')
