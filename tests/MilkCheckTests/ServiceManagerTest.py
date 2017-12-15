# Copyright CEA (2011-2014)
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

'''
This modules defines the tests cases targeting the internal class
RunningTasksManager and the ServiceManager itself
'''

# Classes
import time
from unittest import TestCase
from ClusterShell.NodeSet import NodeSet

from MilkCheck.Engine.BaseEntity import VariableAlreadyExistError
from MilkCheck.Engine.Action import Action
from MilkCheck.Engine.Service import Service
from MilkCheck.Engine.ServiceGroup import ServiceGroup
from MilkCheck.ServiceManager import ServiceManager
from MilkCheck.ServiceManager import ServiceAlreadyReferencedError
from MilkCheck.ServiceManager import ServiceNotFoundError

# Symbols
from MilkCheck.Engine.BaseEntity import NO_STATUS, DONE, REQUIRE_WEAK
from MilkCheck.Engine.BaseEntity import DEP_ERROR, ERROR, WARNING

class ServiceManagerTest(TestCase):
    '''Tests cases for the class ServiceManager'''

    def test_service_registration(self):
        '''Test the resgistration of a service within the manager'''
        manager = ServiceManager()
        srvtest = Service('test')
        manager.register_service(srvtest)
        self.assertTrue(manager.has_service(srvtest))
        self.assertRaises(ServiceAlreadyReferencedError,
            manager.register_service, Service('test'))
        srva = Service('A')
        srvb = Service('B')
        manager.register_services(srva, srvb)
        self.assertTrue(manager.has_service(srva))
        self.assertTrue(manager.has_service(srvb))

    def test_forget_service(self):
        '''The how the manager forgets a service properly'''
        manager = ServiceManager()
        s1 = Service('S1')
        s2 = Service('S2')
        s3 = Service('S3')
        s4 = Service('S4')
        s1.add_dep(target=s2)
        s2.add_dep(target=s3)
        s2.add_dep(target=s4)
        manager.register_services(s1, s2, s3, s4)
        manager.forget_service(s1)
        self.assertFalse(manager.has_service(s1))
        self.assertFalse(s1.has_parent_dep('S2'))
        self.assertFalse(s2.has_child_dep('S1'))
        manager.forget_services(s2, s4)
        self.assertFalse(manager.has_service(s2))
        self.assertFalse(manager.has_service(s4))
        self.assertFalse(s4.has_child_dep('S3'))
        self.assertFalse(s3.has_parent_dep('S4'))

    def test_call_services_case1(self):
        '''Test call of a required service (start S2)'''
        manager = ServiceManager()
        s1 = Service('S1')
        s2 = Service('S2')
        s3 = Service('S3')
        s4 = Service('S4')
        s1.add_action(Action('start', command='/bin/true'))
        s2.add_action(Action('start', command='/bin/true'))
        s3.add_action(Action('start', command='/bin/true'))
        s4.add_action(Action('start', command='/bin/true'))
        s1.add_dep(target=s2)
        s2.add_dep(target=s3)
        s2.add_dep(target=s4)
        manager.register_services(s1, s2, s3, s4)
        manager.call_services(['S2'], 'start')
        self.assertTrue(manager.status not in (ERROR, DEP_ERROR, WARNING))
        self.assertEqual(s1.status, NO_STATUS)
        self.assertEqual(s2.status, DONE)
        self.assertEqual(s3.status, DONE)
        self.assertEqual(s4.status, DONE)
    
    def test_call_services_case2(self):
        '''Test call of required services (start S3, S4)'''
        manager = ServiceManager()
        s1 = Service('S1')
        s2 = Service('S2')
        s3 = Service('S3')
        s4 = Service('S4')
        s1.add_action(Action('start', command='/bin/true'))
        s2.add_action(Action('start', command='/bin/true'))
        s3.add_action(Action('start', command='/bin/true'))
        s4.add_action(Action('start', command='/bin/true'))
        s1.add_dep(target=s2)
        s2.add_dep(target=s3)
        s2.add_dep(target=s4)
        manager.register_services(s1, s2, s3, s4)
        manager.call_services(['S3','S4'], 'start')
        self.assertTrue(manager.status not in (ERROR, DEP_ERROR, WARNING))
        self.assertEqual(s1.status, NO_STATUS)
        self.assertEqual(s2.status, NO_STATUS)
        self.assertEqual(s3.status, DONE)
        self.assertEqual(s4.status, DONE)

    def test_call_services_case3(self):
        '''Test call without required services so make all (start)'''
        manager = ServiceManager()
        s1 = Service('S1')
        s2 = Service('S2')
        s3 = Service('S3')
        s4 = Service('S4')
        s1.add_action(Action('start', command='/bin/true'))
        s2.add_action(Action('start', command='/bin/true'))
        s3.add_action(Action('start', command='/bin/true'))
        s4.add_action(Action('start', command='/bin/true'))
        s1.add_dep(target=s2)
        s2.add_dep(target=s3)
        s2.add_dep(target=s4)
        manager.register_services(s1, s2, s3, s4)
        manager.call_services([], 'start')
        self.assertTrue(manager.status not in (ERROR, DEP_ERROR, WARNING))
        self.assertEqual(s1.status, DONE)
        self.assertEqual(s2.status, DONE)
        self.assertEqual(s3.status, DONE)
        self.assertEqual(s4.status, DONE)

    def test_call_services_retcode0(self):
        '''Test call_services return 0 whether source is DONE'''
        manager = ServiceManager()
        s1 = Service('S1')
        s2 = Service('S2')
        s3 = Service('S3')
        s4 = Service('S4')
        s1.add_action(Action('start', command='/bin/true'))
        s2.add_action(Action('start', command='/bin/true'))
        s3.add_action(Action('start', command='/bin/true'))
        s4.add_action(Action('start', command='/bin/true'))
        s1.add_dep(target=s2)
        s2.add_dep(target=s3)
        s2.add_dep(target=s4)
        manager.register_services(s1, s2, s3, s4)
        manager.call_services([], 'start')
        self.assertTrue(manager.status not in (WARNING, ERROR, DEP_ERROR))

    def test_call_services_retcode_weak(self):
        '''Test call_services return 0 (OK) even with require_weak'''
        manager = ServiceManager()
        s1 = Service('S1')
        s2 = Service('S2')
        s3 = Service('S3')
        s4 = Service('S4')
        s1.add_action(Action('start', command='/bin/true'))
        s2.add_action(Action('start', command='/bin/false'))
        s3.add_action(Action('start', command='/bin/true'))
        s4.add_action(Action('start', command='/bin/true'))
        s1.add_dep(target=s2, sgth=REQUIRE_WEAK)
        s2.add_dep(target=s3)
        s2.add_dep(target=s4)
        manager.register_services(s1, s2, s3, s4)
        manager.call_services([], 'start')
        self.assertEqual(manager.status, DONE)

    def test_call_services_retcode6(self):
        '''Test call_services return 6 whether source is DEP_ERROR'''
        manager = ServiceManager()
        s1 = Service('S1')
        s2 = Service('S2')
        s3 = Service('S3')
        s4 = Service('S4')
        s1.add_action(Action('start', command='/bin/true'))
        s2.add_action(Action('start', command='/bin/false'))
        s3.add_action(Action('start', command='/bin/true'))
        s4.add_action(Action('start', command='/bin/true'))
        s1.add_dep(target=s2)
        s2.add_dep(target=s3)
        s2.add_dep(target=s4)
        manager.register_services(s1, s2, s3, s4)
        manager.call_services([], 'start')
        self.assertTrue(manager.status in (ERROR, DEP_ERROR))

    def test_call_services_case_errors(self):
        '''Test errors generated by call_services'''
        manager = ServiceManager()
        s1 = Service('S1')
        s2 = Service('S2')
        s3 = Service('S3')
        s4 = Service('S4')
        s1.add_action(Action('start', command='%TARGET'))
        s2.add_action(Action('start', command='/bin/true'))
        s3.add_action(Action('start', command='/bin/true'))
        s4.add_action(Action('start', command='/bin/true'))
        s1.add_dep(target=s2)
        s2.add_dep(target=s3)
        s2.add_dep(target=s4)
        manager.register_services(s1, s2, s3, s4)
        self.assertRaises(ServiceNotFoundError,
            manager.call_services, ['S8'], 'start')
        self.assertRaises(ServiceNotFoundError,
            manager.call_services, ['S2', 'S8'], 'start')

    def test_graph(self):
        '''Test DOT graph output'''
        manager = ServiceManager()
        sergrp = ServiceGroup('S1')
        sergrp.fromdict(
           {'services':
                {'srv1':
                     {'target': 'localhost',
                      'actions':
                        {'start': {'cmd':'/bin/True'},
                         'stop': {'cmd': '/bin/False'}},
                      'desc': "I'm the service srv1"
                    },
                'subgroup':
                    {'services':
                        {'svcB':
                            {'require_weak':['svcC'],
                            'actions':
                                {'start': {'cmd': '/bin/True'},
                            '   stop': {'cmd': '/bin/False'}},
                            'desc': 'I am the subservice $NAME'},
                        'svcC':
                            {'actions':
                                {'start': {'cmd': '/bin/True'},
                                'stop': {'cmd': '/bin/False'}},
                                'desc': 'I am the subservice $NAME'}},
                        'target': '127.0.0.1',
                        'desc': "I'm the service $NAME"}},
                })
        manager.register_services(sergrp)
        self.assertEqual(manager.output_graph(), 
"""digraph dependency {
compound=true;
node [style=filled];
subgraph "cluster_S1" {
label="S1";
style=rounded;
node [style=filled];
"S1.__hook" [style=invis];
"S1.srv1";
subgraph "cluster_S1.subgroup" {
label="S1.subgroup";
style=rounded;
node [style=filled];
"S1.subgroup.__hook" [style=invis];
"S1.subgroup.svcB" -> "S1.subgroup.svcC" [style=dashed];
"S1.subgroup.svcC";
}
}
}
""")

    def test_graph_service_exlcude(self):
        """Test the DOT graph output with excluded nodes"""
        ''' Graph:
            E3 -> E2 -> E1 -> D0
                          `-> D1
        '''
        manager = ServiceManager()
        entd0 = Service('D0')
        entd1 = Service('D1')
        ente1 = Service('E1')
        ente2 = Service('E2')
        ente3 = Service('E3')
        ente3.add_dep(ente2)
        ente2.add_dep(ente1)
        ente1.add_dep(entd0)
        ente1.add_dep(entd1)
        manager.register_services(entd0, entd1, ente1, ente2, ente3)
        self.assertEqual(manager.output_graph(excluded=['E2']),
"""digraph dependency {
compound=true;
node [style=filled];
"E1" -> "D0";
"E1" -> "D1";
"D0";
"D1";
}
""")
        self.assertEqual(manager.output_graph(excluded=['D0']),
"""digraph dependency {
compound=true;
node [style=filled];
"D1";
}
""")
        self.assertEqual(manager.output_graph(excluded=['D0', 'D1']),
"""digraph dependency {
compound=true;
node [style=filled];
}
""")

    def test_call_services_reversed(self):
        '''Test service_manager with custom reversed actions'''
        manager = ServiceManager()
        s1 = Service('S1')
        s2 = Service('S2')
        s1.add_action(Action('wait', command='/bin/true'))
        s2.add_action(Action('wait', command='/bin/true'))
        s1.add_dep(s2)
        manager.register_services(s1, s2)
        manager.call_services(['S1'], 'wait',
                        conf={"reverse_actions": ['wait']})
        self.assertTrue(s1._algo_reversed)
        self.assertTrue(s2._algo_reversed)

    def test_call_services_reversed_multiple(self):
        '''Test service_manager with multiple custom reversed actions'''
        manager = ServiceManager()
        s1 = Service('S1')
        s2 = Service('S2')
        s1.add_action(Action('stop', command='/bin/true'))
        s2.add_action(Action('wait', command='/bin/true'))
        manager.register_services(s1, s2)
        actions = ['stop', 'wait']
        for act in actions:
            s1._algo_reversed = False
            s2._algo_reversed = False
            manager.call_services(['S1'], act,
                            conf={"reverse_actions": actions})
            self.assertTrue(s1._algo_reversed)
            self.assertTrue(s2._algo_reversed)

    def test_call_services_parallelism(self):
        '''Test services parallelism'''
        manager = ServiceManager()
        s1 = Service('S1')
        s2 = Service('S2')
        s1.add_action(Action('wait', command='/bin/sleep 0.5'))
        s2.add_action(Action('wait', command='/bin/sleep 0.5'))
        manager.register_services(s1, s2)

        elapsed = time.time()
        manager.call_services(['S1', 'S2'], 'wait')
        elapsed = time.time() - elapsed
        self.assertTrue(elapsed < 0.7, 'Time elapsed too high (%f)' % elapsed)
        self.assertTrue(manager.status not in (ERROR, DEP_ERROR, WARNING))
        self.assertEqual(s1.status, DONE)
        self.assertEqual(s2.status, DONE)

    def test_variable_config_defines_one(self):
        """Test custom defines in variable_config()"""
        manager = ServiceManager()
        manager._variable_config(conf={'defines':['foo=bar']})
        self.assertEqual(manager.variables['foo'], 'bar')

    def test_variable_config_defines_several(self):
        """Test custom defines in variable_config() (2 vars)"""
        manager = ServiceManager()
        manager._variable_config(conf={'defines':['foo=bar', 'baz=buz']})
        self.assertEqual(manager.variables['foo'], 'bar')
        self.assertEqual(manager.variables['baz'], 'buz')

    def test_add_variable_twice(self):
        '''Add a variable twice raises VariableAlreadyExistError'''
        manager = ServiceManager()
        manager.add_var('var', 'foo')
        self.assertRaises(VariableAlreadyExistError, manager.add_var, 'var', 'foo')

    def test_remove_variable(self):
        '''Remove a variable, defined or not, is fine.'''
        manager = ServiceManager()
        manager.add_var('var', 'foo')
        self.assertEqual(manager.variables['var'], 'foo')

        # Remove it
        manager.remove_var('var')
        self.assertTrue('foo' not in manager.variables)

    def test_variable_resolution(self):
        """Resolve top-scope variable"""
        manager = ServiceManager()
        manager.add_var('var', '%(echo -n foo)')
        manager.add_var('var2', '%var')
        svc = Service('svc')
        svc.add_action(Action('start', command='start %var2'))
        manager.register_services(svc)
        manager.resolve_all()
        self.assertEqual(manager.variables['var'], 'foo')
        self.assertEqual(manager.variables['var2'], 'foo')

    def test_empty_only_nodes(self):
        '''Test_apply_config with empty nodeset in only_nodes'''
        empty_ns = NodeSet()
        manager = ServiceManager()
        s1 = Service('S1', target = NodeSet("localhost"))
        manager.register_services(s1)
        conf = {'only_nodes': empty_ns}
        manager._apply_config(conf)
        self.assertEqual(s1.target, empty_ns)

    def test_empty_excluded_nodes(self):
        '''Test _apply_config with empty nodeset in excluded_nodes'''
        localhost_ns = NodeSet("localhost")
        manager = ServiceManager()
        s1 = Service('S1', target = localhost_ns)
        manager.register_services(s1)
        conf = {'excluded_nodes': NodeSet()}
        manager._apply_config(conf)
        self.assertEqual(s1.target, localhost_ns)

    def test_tagged_run(self):
        """Test that services without the configuration tags are skipped"""
        manager = ServiceManager()
        srv = Service('service')
        srv.fromdict({
                      'target': 'localhost',
                      'tags': ['foo'],
                      'desc': "I'm a service",
                      'actions': {'start': {'cmd': '/bin/true'}},
                     })
        manager.register_services(srv)
        manager._apply_config({'tags': set(['foo'])})
        self.assertFalse(srv.to_skip('start'))
        manager._apply_config({'tags': set(['bar'])})
        self.assertTrue(srv.to_skip('start'))
