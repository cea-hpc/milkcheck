#
# Copyright CEA (2011-2017)
#

from unittest import TestCase
from MilkCheck.Config.Configuration import MilkCheckConfig, ConfigurationError
from MilkCheck.Config.Configuration import UnknownDependencyError
from MilkCheck.ServiceManager import service_manager_self, ServiceManager

import textwrap
import socket
HOSTNAME = socket.gethostname().split('.')[0]

class MilkCheckConfigTest(TestCase):
    '''Define the test cases of the class MilkCheckConfig'''

    def tearDown(self):
        ServiceManager._instance = None

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
        self.cfg._build_services()
        # Get back the manager
        manager = service_manager_self()
        self.assertTrue('S1' in manager.entities)
        self.assertTrue('S2' in manager.entities)
        self.assertTrue('S3' in manager.entities)
        self.assertTrue('S4' in manager.entities)
        self.assertTrue(manager.entities['S1'].has_parent_dep('S2'))
        self.assertTrue(manager.entities['S1'].has_parent_dep('S3'))
        self.assertTrue(manager.entities['S3'].has_parent_dep('S4'))
        self.assertTrue(manager.entities['S2'].has_parent_dep('S4'))
        self.assertTrue(manager.entities['S4'].has_parent_dep('G1'))

    def test_parsing_deps(self):
        '''Test parsing of dependencies within a dictionnary'''
        wrap = self.cfg._parse_deps({'require': ['S1'], 'check': ['S2']})
        self.assertTrue(wrap)
        self.assertTrue('S1' in wrap.deps['require'])
        self.assertTrue('S2' in wrap.deps['check'])
        self.assertFalse(wrap.deps['require_weak'])

        wrap = self.cfg._parse_deps({})
        self.assertTrue(wrap)
        self.assertFalse(wrap.deps['require'])
        self.assertFalse(wrap.deps['check'])
        self.assertFalse(wrap.deps['require_weak'])

        wrap = self.cfg._parse_deps({'require': ['s1'], 'filter': ['s2']})
        self.assertTrue(wrap)
        self.assertTrue('s1' in wrap.deps['require'])
        self.assertTrue('s2' in wrap.deps['filter'])
        self.assertFalse(wrap.deps['require_weak'])

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
        self.cfg.build_graph()
        self.assertTrue(self.cfg._flow)
        self.assertTrue(len(self.cfg._flow) == 1)

    def test_parse_with_services_syntax(self):
        '''Test loading with empty YAML document in flow.'''
        self.cfg.load_from_stream('''---
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
                cmd: run_bar''')

        self.cfg.build_graph()
        # Get back the manager
        manager = service_manager_self()
        self.assertTrue('foo1' in manager.entities)
        self.assertTrue('foo2' in manager.entities)
        self.assertTrue('bar' in manager.entities)
        self.assertTrue(manager.entities['foo1'].has_action('start'))
        self.assertTrue(manager.entities['foo1'].has_parent_dep('bar'))
        self.assertTrue(manager.entities['foo2'].has_action('start'))
        self.assertTrue(manager.entities['foo2'].has_parent_dep('bar'))
        self.assertTrue(manager.entities['bar'].has_action('start'))

    def test_parse_with_compat_syntax(self):
        '''Test loading with empty YAML document in flow.'''
        self.cfg.load_from_stream('''
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
                cmd: run_bar''')

        self.cfg.build_graph()
        # Get back the manager
        manager = service_manager_self()
        self.assertTrue('compat' in manager.entities)
        self.assertTrue('foo1' in manager.entities)
        self.assertTrue('foo2' in manager.entities)
        self.assertTrue('bar' in manager.entities)
        self.assertTrue('compat_grp' in manager.entities)
        self.assertTrue(manager.entities['foo1'].has_action('start'))
        self.assertTrue(manager.entities['foo1'].has_parent_dep('bar'))
        self.assertTrue(manager.entities['foo2'].has_action('start'))
        self.assertTrue(manager.entities['foo2'].has_parent_dep('bar'))
        self.assertTrue(manager.entities['bar'].has_action('start'))
        self.assertTrue(manager.entities['compat_grp'].has_parent_dep('compat'))

    def test_missing_dep(self):
        """Using a missing dep raises UnknownDependencyError"""
        self.cfg.load_from_stream('''
services:
    foo:
        require: [ bad ]
        actions:
            start:
                cmd: /bin/true''')
        self.assertRaises(UnknownDependencyError, self.cfg.build_graph)

    def test_deps_between_top_services(self):
        '''Deps between 2 services in top "services" section are ok'''
        self.cfg.load_from_stream('''
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
                cmd: run_bar''')
        self.cfg.build_graph()
        manager = service_manager_self()
        self.assertTrue('foo' in manager.entities)
        self.assertTrue('bar' in manager.entities)
        self.assertTrue(manager.entities['foo'].has_action('start'))
        self.assertTrue(manager.entities['bar'].has_action('start'))
        self.assertTrue(manager.entities['bar'].has_parent_dep('foo'))

    def test_before_rule_parsing(self):
        """'before' is supported in configuration (only for compatibility)"""
        self.cfg.load_from_stream('''
services:
    foo:
        actions:
            start:
                cmd: run %NAME
    bar:
        before: [ 'foo' ]
        actions:
            start:
                cmd: run_bar''')
        self.cfg.build_graph()
        manager = service_manager_self()
        self.assertTrue('foo' in manager.entities)
        self.assertTrue('bar' in manager.entities)
        self.assertTrue(manager.entities['bar'].has_parent_dep('foo'))

    def test_after_rule_parsing(self):
        """'after' is supported in configuration"""
        self.cfg.load_from_stream('''
services:
    foo:
        actions:
            start:
                cmd: run %NAME
    bar:
        after: [ 'foo' ]
        actions:
            start:
                cmd: run_bar''')
        self.cfg.build_graph()
        manager = service_manager_self()
        self.assertTrue('foo' in manager.entities)
        self.assertTrue('bar' in manager.entities)
        self.assertTrue(manager.entities['bar'].has_parent_dep('foo'))

    def test_filter_rule_parsing(self):
        """'filter' is supported in configuration"""
        self.cfg.load_from_stream('''
services:
    foo:
        actions:
            start:
                cmd: run %NAME
    bar:
        filter: [ 'foo' ]
        actions:
            start:
                cmd: run_bar''')
        self.cfg.build_graph()
        manager = service_manager_self()
        self.assertTrue('foo' in manager.entities)
        self.assertTrue('bar' in manager.entities)
        self.assertTrue(manager.entities['bar'].has_parent_dep('foo'))

    def test_bad_rule(self):
        """Unknown rule raises ConfigurationError"""
        self.cfg.load_from_stream('''
services:
    foo:
        actions:
            start:
                cmd: run %NAME
badrule: foo''')
        self.assertRaises(ConfigurationError, self.cfg.build_graph)

    def test_loading_variables_after_services(self):
        '''
        Test parsing of a Yaml flow with variables referenced before
        their definition in another file.
        '''
        self.cfg.load_from_stream('''
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
    LUSTRE_FS_LIST: store0,work0''')

        self.cfg.build_graph()

        srv = service_manager_self().entities['S1']
        srv.resolve_all()
        self.assertTrue('LUSTRE_FS_LIST' in service_manager_self().variables)
        self.assertTrue('TARGET_VAR' in service_manager_self().variables)
        self.assertEqual(str(srv.target), "foo")
        self.assertEqual(srv._actions['start'].command, "echo store0,work0")
        self.assertTrue(len(self.cfg._flow) == 2)

    def test_set_variables_before_configuration_parsing(self):
        '''
        Test parsing of Yaml flow with variables prevously defined
        '''
        manager = service_manager_self()
        manager.add_var('MY_VAR', 'bar')
        self.cfg.load_from_stream('''
variables:
    MY_VAR: foo
---
services:
     S1:
            desc: "I'm the service S1"
            actions:
                start:
                    cmd: echo %MY_VAR''')
        self.cfg.build_graph()
        self.assertTrue(manager.variables['MY_VAR'] == 'bar')

    def test_variables_with_escaping_pattern(self):
        """configuration should not resolve variables"""
        self.cfg.load_from_stream(textwrap.dedent("""
                        services:
                            svc:
                                variables:
                                    foo: nice
                                actions:
                                    start:
                                        cmd: shine config -O %%host %foo"""))
        self.cfg.build_graph()
        svc = service_manager_self().entities['svc']
        # Should not resolve variables at this stage. This should be done later.
        self.assertEqual(svc._actions['start'].command, "shine config -O %%host %foo")

    def test_variables_with_dependency(self):
        """
        Test instantiate a service from a dictionnary with variables in dependency
        """
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
                    variables:
                        limit: 1
                    require: "%DEPS"
                    timeout: "%limit"
                    desc: "Service %SERVICE with timeout %limit"
                    actions:
                        start:
                            cmd: service %SERVICE start"""))
        self.cfg.build_graph()
        s1 = service_manager_self().entities['s1']
        s1.resolve_all()
        wrap = self.cfg._parse_deps({'require': "%DEPS"}, s1)
        self.assertTrue('s2' in wrap.deps['require'])
        self.assertTrue('s3' in wrap.deps['require'])
        self.assertEqual(s1.desc, "Service s1 with timeout 1")
        self.assertEqual(s1.timeout, 1)
        self.assertEqual(s1._actions['start'].command, "service s1 start")
        self.assertEqual(s1._actions['start'].desc, "Service s1 with timeout 1")
        self.assertEqual(s1._actions['start'].timeout, 1)
