#
# Copyright CEA (2011-2017)
#

import os
import tempfile
import textwrap
import unittest

from MilkCheck.Config.Configuration import load_from_stream, load_from_dir, \
                                           ConfigurationError

def _mktmpfile(content, dir=None, suffix='.yaml'):
    tmpfile = tempfile.NamedTemporaryFile(suffix=suffix, dir=dir)
    tmpfile.write(textwrap.dedent(content))
    tmpfile.flush()
    return tmpfile


class MilkCheckConfigTest(unittest.TestCase):
    """Test for load_from_stream(), load_from_dir()"""

    #
    # load_from_dir()
    #

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

    #
    # load_from_stream()
    #

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
        """Unknown rule raises ConfigurationError"""
        flow = textwrap.dedent("""
            services:
                foo:
                    actions:
                        start:
                            cmd: run %NAME
            badrule: foo""")
        self.assertRaises(ConfigurationError, load_from_stream, flow)

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
