#
# Copyright CEA (2011-2017)
#

from unittest import TestCase
from MilkCheck.Config.Configuration import MilkCheckConfig, ConfigurationError

import textwrap
import socket
HOSTNAME = socket.gethostname().split('.')[0]

class MilkCheckConfigTest(TestCase):
    '''Define the test cases of the class MilkCheckConfig'''

    def setUp(self):
        self.cfg = MilkCheckConfig()

    def test_loading_conf_from_stream(self):
        '''Test parsing of a Yaml flow trough a stream'''
        self.cfg.load_from_stream('''services:
     S1:
            desc: "I'm the service S1"
            variables:
                LUSTRE_FS_LIST: store0,work0
            target: "%s"
            actions:
                start:
                    check: [ status ]
                    cmd:   shine mount -q -L -f $LUSTRE_FS_LIST
                stop:
                    cmd:   shine umount -q -L -f $LUSTRE_FS_LIST
                status:
                    cmd :  shine status -q -L -f $LUSTRE_FS_LIST
                check:
                    check: [ status ]''' % HOSTNAME)
        self.assertTrue(self.cfg._flow)
        self.assertTrue(len(self.cfg._flow) == 1)

    def test_loading_conf_from_dir(self):
        '''Test parsing of a Yaml existing in a directory'''
        dty = '../tests/MilkCheckTests/ConfigTests/YamlTestFiles/'
        self.cfg.load_from_dir(directory=dty)
        self.assertTrue(self.cfg.data_flow)
        self.cfg.load_from_dir(directory=dty, recursive=True)
        self.assertTrue(self.cfg.data_flow)

    def test_loading_conf_farom_baddir(self):
        '''Test load in a directory that doesn't exist'''
        dty = '/nowhere'
        self.assertRaises(ValueError, self.cfg.load_from_dir, directory=dty)

    def test_load_from_stream(self):
        '''Test parsing of a single YAML stream'''
        flow = open('../tests/MilkCheckTests/ConfigTests/'
                    'YamlTestFiles/sample_1/sample_1.yaml')
        self.cfg.load_from_stream(flow)
        flow.close()
        self.assertTrue(self.cfg.data_flow)
        self.assertEqual(len(self.cfg.data_flow), 2)

    def test_building_graph(self):
        '''Test graph building from configuration'''
        dty = '../tests/MilkCheckTests/ConfigTests/YamlTestFiles/sample_1/'
        self.cfg.load_from_dir(dty)
        merged = self.cfg.merge_flow()
        self.assertTrue('S1' in merged['services'])
        self.assertTrue('S2' in merged['services'])
        self.assertTrue('S3' in merged['services'])
        self.assertTrue('S4' in merged['services'])
        self.assertEqual(merged['services']['S1']['require'], ['S2', 'S3'])
        self.assertEqual(merged['services']['S3']['require'], ['S4'])
        self.assertEqual(merged['services']['S2']['require'], ['S4'])
        self.assertEqual(merged['services']['S4']['require_weak'], ['G1'])

    def test_load_with_empty_yaml_document(self):
        '''Test loading with empty YAML document in flow.'''
        self.cfg = MilkCheckConfig()
        self.cfg.load_from_stream('''---
# This is en empty document.
---
services:
    S1:
            desc: "I'm the service S1"
            variables:
                LUSTRE_FS_LIST: store0,work0
            target: "%s"
            actions:
                start:
                    check: [ status ]
                    cmd:   shine mount -q -L -f $LUSTRE_FS_LIST
                stop:
                    cmd:   shine umount -q -L -f $LUSTRE_FS_LIST
                status:
                    cmd :  shine status -q -L -f $LUSTRE_FS_LIST
                check:
                    check: [ status ]''' % HOSTNAME)
        self.assertTrue(self.cfg._flow)
        self.assertTrue(len(self.cfg._flow) == 1)

    def test_parse_with_services_syntax(self):
        """Test configuration with 'services' top syntax"""
        self.cfg.load_from_stream(textwrap.dedent('''
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
        self.assertEqual(self.cfg.merge_flow(), merged)

    def test_parse_with_compat_syntax(self):
        '''Test loading with empty YAML document in flow.'''
        self.cfg.load_from_stream(textwrap.dedent('''
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
        self.assertEqual(self.cfg.merge_flow(), merged)

    def test_deps_between_top_services(self):
        """Merge 2 'services' at top scope"""
        self.cfg.load_from_stream(textwrap.dedent("""
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
        self.assertEqual(self.cfg.merge_flow(), merged)

    def test_bad_rule(self):
        """Unknown rule raises ConfigurationError"""
        self.cfg.load_from_stream('''
services:
    foo:
        actions:
            start:
                cmd: run %NAME
badrule: foo''')
        self.assertRaises(ConfigurationError, self.cfg.merge_flow)

    def test_loading_variables_after_services(self):
        """Parse with 'variables' section after service definitions."""
        self.cfg.load_from_stream(textwrap.dedent("""
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
        self.assertEqual(self.cfg.merge_flow(), merged)

    def test_parse_with_variables_service_top_scope(self):
        """Test with 'variables' and 'services' at top scope"""
        self.cfg.load_from_stream(textwrap.dedent("""
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
        self.assertEqual(self.cfg.merge_flow(), merged)
