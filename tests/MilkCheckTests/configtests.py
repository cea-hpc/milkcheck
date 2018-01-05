#
# Copyright CEA (2011-2018)
#
# Contributors:
#  Aurelien Cedeyn <aurelien.cedeyn@cea.fr>
#

import logging
import optparse
import os
import tempfile
import textwrap
import unittest

from MilkCheck.config import ConfigParser, ConfigError, load_from_stream, \
                             load_from_dir

def _mktmpfile(content, dir=None, suffix='.yaml'):
    tmpfile = tempfile.NamedTemporaryFile(suffix=suffix, dir=dir)
    tmpfile.write(textwrap.dedent(content))
    tmpfile.flush()
    return tmpfile

class MockConfigParser(ConfigParser):
    '''Class to overwrite CONFIGPATH and avoid logging setup'''
    CONFIG_PATH = '/nowhere'
    @staticmethod
    def install_logger(verbose=0, debug=False):
        '''Return a silent logger'''
        return logging.getLogger('milkcheck')

class ConfigParserTest(unittest.TestCase):
    '''Define the test cases of the class ConfigParser'''
    def setUp(self):
        '''Setup empty options'''
        self._options = optparse.Values()
        setattr(self._options, 'verbosity', 0)
        setattr(self._options, 'debug', False)

    def test_instanciation(self):
        '''Try to instanciate an object of the class ConfigParser'''
        self.assertTrue(MockConfigParser(self._options))

    def test_no_configuration_file(self):
        '''Test if can not access to the configuration file'''
        config = MockConfigParser(self._options)
        for key in ConfigParser.DEFAULT_FIELDS.iterkeys():
            self.assertEqual(config[key], ConfigParser.DEFAULT_FIELDS[key]['value'])
            self.assertEqual(type(config[key]), ConfigParser.DEFAULT_FIELDS[key]['type'])

    def test_check_data(self):
        """YAML flow is correctly parsed"""
        config = MockConfigParser(self._options)
        config._check_data({'fanout': 27})
        self.assertEqual(config['fanout'], 27)

    def test_check_data_type(self):
        """Option type is correctly checked"""
        config = MockConfigParser(self._options)
        # Element does not exist
        self.assertRaises(ConfigError, config._check_data, {'sugar': 'yes'})
        # Element has a bad type
        self.assertRaises(ConfigError, config._check_data, {'fanout': [27, 28]})

    def test_check_data_allowed_values(self):
        """Option value is correctly checked"""
        config = MockConfigParser(self._options)
        # Value is not allowed
        self.assertRaises(ConfigError, config._check_data, {'report':'invalid'})
        # Allowed value for report
        for value in ('full', 'no', 'default'):
            config._check_data({'report': value})
            self.assertEqual(config['report'], value)

    def test_check_summary_compat(self):
        """Check compat with summary"""
        setattr(self._options, 'summary', True)
        config = MockConfigParser(self._options)
        self.assertEqual(config['report'], 'default')

        setattr(self._options, 'summary', False)
        config = MockConfigParser(self._options)
        self.assertEqual(config['report'],
                         ConfigParser.DEFAULT_FIELDS['report']['value'])

        setattr(self._options, 'summary', True)
        setattr(self._options, 'report', 'full')
        config = MockConfigParser(self._options)
        self.assertEqual(config['report'], 'full')

    def test_parsing_sample_configuration(self):
        """Parse sample configuration file"""
        class MockLocalConfigParser(MockConfigParser):
            CONFIG_PATH = '../conf/milkcheck.conf'

        config = MockLocalConfigParser(self._options)
        self.assertEqual(config['report'], 'no')
        self.assertEqual(config['fanout'], 64)
        self.assertEqual(config['config_dir'], '/etc/milkcheck/conf')
        self.assertEqual(config['reverse_actions'], ['stop'])

    def test_parsing_summary(self):
        """Parse configuration file with summary option (compat)"""
        tmpfile = tempfile.NamedTemporaryFile()
        tmpfile.write("summary: True\n")
        tmpfile.flush()

        class MockSummaryLocalConfigParser(MockConfigParser):
            CONFIG_PATH = tmpfile.name
        config = MockSummaryLocalConfigParser(self._options)
        self.assertEqual(config['summary'], True)


class LoadFromDirTest(unittest.TestCase):
    """Test for load_from_dir()"""

    def test_load_conf_from_baddir(self):
        '''Test load in a directory that doesn't exist'''
        self.assertRaises(ValueError, load_from_dir, directory='/doesnot/exist')

    def test_load_from_dir(self):
        """load a directory with a simple YAML file"""
        try:
            tmpdir = tempfile.mkdtemp(prefix='test-mlk-')
            tmpfile = _mktmpfile(dir=tmpdir, content="""
                services:
                    svc1:
                        actions:
                            start:
                                cmd: /bin/true
                    svc2:
                        require: [svc1]
                        actions:
                            start:
                                cmd: /bin/false
                    """)

            flow = load_from_dir(tmpdir)
            merged = {
                'services': {
                    'svc1': {
                        'actions': {'start': {'cmd': '/bin/true'}}
                    },
                    'svc2': {
                        'require': ['svc1'],
                        'actions': {'start': {'cmd': '/bin/false'}}
                    }
                }
            }
            self.assertEqual(merged, flow)

        finally:
            tmpfile.close()
            os.rmdir(tmpdir)

    def test_load_from_dir_multiple_files(self):
        """load a directory with multiple YAML files"""
        try:
            tmpdir = tempfile.mkdtemp(prefix='test-mlk-')
            subtmpdir = tempfile.mkdtemp(prefix='test-mlk-', dir=tmpdir)
            tmpfile1 = _mktmpfile(dir=tmpdir, content="""
                    services:
                        svc1:
                            actions:
                                start:
                                    cmd: /bin/true
                    """)
            tmpfile2 = _mktmpfile(dir=tmpdir, content="""
                    services:
                        svc2:
                            actions:
                                start:
                                    cmd: /bin/false
                    """)
            tmpfile3 = _mktmpfile(dir=subtmpdir, content="""
                    services:
                        svc3:
                            actions:
                                start:
                                    cmd: echo 3
                    """)
            tmpfile_bad = _mktmpfile(dir=tmpdir, suffix='.not',
                                  content="(NOT A YAML SYNTAX")

            # Test without recursion
            flow = load_from_dir(tmpdir, recursive=False)
            merged = {
                'services': {
                    'svc1': {
                        'actions': {'start': {'cmd': '/bin/true'}}
                    },
                    'svc2': {
                        'actions': {'start': {'cmd': '/bin/false'}}
                    }
                }
            }
            self.assertEqual(merged, flow)

            # Test WITH recursion
            flow = load_from_dir(tmpdir, recursive=True)
            merged = {
                'services': {
                    'svc1': {
                        'actions': {'start': {'cmd': '/bin/true'}}
                    },
                    'svc2': {
                        'actions': {'start': {'cmd': '/bin/false'}}
                    },
                    'svc3': {
                        'actions': {'start': {'cmd': 'echo 3'}}
                    }
                }
            }
            self.assertEqual(merged, flow)

        finally:
            tmpfile3.close()
            tmpfile2.close()
            tmpfile1.close()
            tmpfile_bad.close()
            os.rmdir(subtmpdir)
            os.rmdir(tmpdir)


class LoadFromStreamTest(unittest.TestCase):
    """Test for load_from_stream()"""

    def test_loading_conf_from_stream(self):
        '''Test parsing of a Yaml flow trough a stream'''
        flow = load_from_stream(textwrap.dedent("""
            services:
                foo:
                    actions:
                        start:
                            cmd: run_foo"""))
        merged = {
            'services': {
                'foo': {
                    'actions': {'start': {'cmd': 'run_foo'}}
                }
            }
        }
        self.assertEqual(flow, merged)

    def test_load_from_file(self):
        """load a stream from a file object"""
        tmp = tempfile.NamedTemporaryFile(prefix='milkcheck-test-')
        tmp.write(textwrap.dedent("""
            ---
            variables:
                command: run_bar
            ---
            services:
                bar:
                    actions:
                        start:
                            cmd: '%command'"""))
        tmp.flush()
        flow = load_from_stream(open(tmp.name))
        merged = {
            'variables': {'command': 'run_bar'},
            'services': {
                'bar': {
                    'actions': {'start': {'cmd': '%command'}}
                }
            }
        }
        self.assertEqual(flow, merged)

    def test_load_with_empty_yaml_document(self):
        '''Test loading with empty YAML document in flow.'''
        flow = load_from_stream(textwrap.dedent("""
            ---
            # This is an empty document.
            ---
            services:
                S1:
                    target: "foo"
                    actions:
                        start:
                            check: [ status ]
                            cmd:   shine mount -q -L -f store0
                        status:
                            cmd :  shine status -q -L -f store0
                        check:
                            check: [ status ]"""))
        merged = {
            'services': {
                'S1': {
                    'target': 'foo',
                    'actions': {
                        'start': {
                            'check': ['status'],
                            'cmd': 'shine mount -q -L -f store0'
                        },
                        'status': {'cmd': 'shine status -q -L -f store0'},
                        'check': {'check': ['status']}
                    }
                }
            }
        }
        self.assertEqual(flow, merged)

    def test_parse_with_services_syntax(self):
        """Test configuration with 'services' top syntax"""
        flow = load_from_stream(textwrap.dedent('''
            ---
            services:
                foo[1-2]:
                    desc: "this is desc"
                    require: [ 'bar' ]
                    actions:
                        start:
                            cmd: run %NAME
                bar:
                    actions:
                        start:
                            cmd: run_bar'''))
        merged = {
            'services': {
                'foo[1-2]': {
                    'desc': 'this is desc',
                    'require': ['bar'],
                    'actions': {
                        'start': {'cmd': 'run %NAME'}
                    }
                },
                'bar': {
                    'actions': {
                        'start': {'cmd': 'run_bar'}
                    }
                }
            }
        }
        self.assertEqual(flow, merged)

    def test_parse_with_compat_syntax(self):
        """Test loading with compat 'service' syntax at top scope"""
        flow = load_from_stream(textwrap.dedent('''
            service:
                name: compat
                actions:
                    start:
                        cmd: echo foo
            ---
            service:
                name: compat_grp
                require: compat
                services:
                    subsvc:
                        actions:
                            start:
                                cmd: echo foo
            ---
            services:
                foo[1-2]:
                    desc: "this is desc"
                    require: [ 'bar' ]
                    actions:
                        start:
                            cmd: run %NAME
                bar:
                    actions:
                        start:
                            cmd: run_bar'''))
        merged = {
            'services': {
                'compat': {
                    'actions': {'start': {'cmd': 'echo foo'}}
                },
                'compat_grp': {
                    'require': 'compat',
                    'services': {
                        'subsvc': {
                            'actions': {'start': {'cmd': 'echo foo'}}
                        }
                    }
                },
                'foo[1-2]': {
                    'desc': 'this is desc',
                    'require': ['bar'],
                    'actions': {'start': {'cmd': 'run %NAME'}}
                },
                'bar': {
                    'actions': {'start': {'cmd': 'run_bar'}}
                }
            }
        }
        self.assertEqual(flow, merged)

    def test_deps_between_top_services(self):
        """Merge 2 'services' at top scope"""
        flow = load_from_stream(textwrap.dedent("""
            services:
                foo:
                    actions:
                        start:
                            cmd: run %NAME
            ---
            services:
                bar:
                    require: [ 'foo' ]
                    actions:
                        start:
                            cmd: run_bar"""))
        merged = {
            'services': {
                'foo': {
                    'actions': {'start': {'cmd': 'run %NAME'}}
                },
                'bar': {
                    'require': ['foo'],
                    'actions': {'start': {'cmd': 'run_bar'}}
                }
            }
        }
        self.assertEqual(flow, merged)

    def test_bad_rule(self):
        """Unknown rule raises ConfigError"""
        flow = textwrap.dedent("""
            services:
                foo:
                    actions:
                        start:
                            cmd: run %NAME
            badrule: foo""")
        self.assertRaises(ConfigError, load_from_stream, flow)

    def test_loading_variables_after_services(self):
        """Parse with 'variables' section after service definitions."""
        flow = load_from_stream(textwrap.dedent("""
            services:
                 S1:
                    desc: "I'm the service S1"
                    target: "%TARGET_VAR"
                    actions:
                        start:
                            cmd: echo %LUSTRE_FS_LIST
            ---
            variables:
                TARGET_VAR: foo
                LUSTRE_FS_LIST: store0,work0"""))
        merged = {
            'variables': {
                'TARGET_VAR': 'foo',
                'LUSTRE_FS_LIST': 'store0,work0'
            },
            'services': {
                'S1': {
                    'desc': "I'm the service S1",
                    'target': "%TARGET_VAR",
                    'actions': {'start': {'cmd': 'echo %LUSTRE_FS_LIST'}}
                }
            }
        }
        self.assertEqual(flow, merged)

    def test_parse_with_variables_service_top_scope(self):
        """Test with 'variables' and 'services' at top scope"""
        flow = load_from_stream(textwrap.dedent("""
            variables:
                DEPS: [ s2, s3 ]
            ---
            services:
                s2:
                    actions:
                        start:
                            cmd: /bin/true
                s3:
                    actions:
                        start:
                            cmd: /bin/true
                s1:
                    require: "%DEPS"
                    actions:
                        start:
                            cmd: service %SERVICE start"""))
        merged = {
            'variables': {
                'DEPS': ['s2', 's3']
            },
            'services': {
                's3': {
                    'actions': {'start': {'cmd': '/bin/true'}}
                },
                's2': {
                    'actions': {'start': {'cmd': '/bin/true'}}
                },
                's1': {
                    'require': '%DEPS',
                    'actions': {'start': {'cmd': 'service %SERVICE start'}}
                }
            }
        }
        self.assertEqual(flow, merged)
