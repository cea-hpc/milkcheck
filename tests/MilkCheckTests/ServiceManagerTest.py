# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

'''
This modules defines the tests cases targeting the internal class
RunningTasksManager and the ServiceManager itself
'''

# Classes
from unittest import TestCase
from ClusterShell.NodeSet import NodeSet
from MilkCheck.Engine.Service import Service, ActionNotFoundError
from MilkCheck.Engine.Action import Action
from MilkCheck.ServiceManager import ServiceManager, service_manager_self
from MilkCheck.ServiceManager import ServiceAlreadyReferencedError
from MilkCheck.ServiceManager import ServiceNotFoundError

# Symbols
from MilkCheck.Engine.BaseEntity import NO_STATUS, DONE

class ServiceManagerTest(TestCase):
    '''Tests cases for the class ServiceManager'''
    def setUp(self):
        ServiceManager._instance = None

    def tearDown(self):
        ServiceManager._instance = None

    def test_instanciation(self):
        '''Test the instanciation of the singleton class ServiceManager'''
        manager = service_manager_self()
        same_manager = service_manager_self()
        self.assertTrue(manager is same_manager)

    def test_service_registration(self):
        '''Test the resgistration of a service within the manager'''
        manager = service_manager_self()
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
        manager = service_manager_self()
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
        manager = service_manager_self()
        s1 = Service('S1')
        s2 = Service('S2')
        s3 = Service('S3')
        s4 = Service('S4')
        s1.add_action(Action('start', 'localhost', '/bin/true'))
        s2.add_action(Action('start', 'localhost', '/bin/true'))
        s3.add_action(Action('start', 'localhost', '/bin/true'))
        s4.add_action(Action('start', 'localhost', '/bin/true'))
        s1.add_dep(target=s2)
        s2.add_dep(target=s3)
        s2.add_dep(target=s4)
        manager.register_services(s1, s2, s3, s4)
        manager.call_services(['S2'], 'start')
        self.assertEqual(s1.status, NO_STATUS)
        self.assertEqual(s2.status, DONE)
        self.assertEqual(s3.status, DONE)
        self.assertEqual(s4.status, DONE)
    
    def test_call_services_case2(self):
        '''Test call of required services (start S3, S4)'''
        manager = service_manager_self()
        s1 = Service('S1')
        s2 = Service('S2')
        s3 = Service('S3')
        s4 = Service('S4')
        s1.add_action(Action('start', 'localhost', '/bin/true'))
        s2.add_action(Action('start', 'localhost', '/bin/true'))
        s3.add_action(Action('start', 'localhost', '/bin/true'))
        s4.add_action(Action('start', 'localhost', '/bin/true'))
        s1.add_dep(target=s2)
        s2.add_dep(target=s3)
        s2.add_dep(target=s4)
        manager.register_services(s1, s2, s3, s4)
        manager.call_services(['S3','S4'], 'start')
        self.assertEqual(s1.status, NO_STATUS)
        self.assertEqual(s2.status, NO_STATUS)
        self.assertEqual(s3.status, DONE)
        self.assertEqual(s4.status, DONE)

    def test_call_services_case3(self):
        '''Test call without required services so make all (start)'''
        manager = service_manager_self()
        s1 = Service('S1')
        s2 = Service('S2')
        s3 = Service('S3')
        s4 = Service('S4')
        s1.add_action(Action('start', 'localhost', '/bin/true'))
        s2.add_action(Action('start', 'localhost', '/bin/true'))
        s3.add_action(Action('start', 'localhost', '/bin/true'))
        s4.add_action(Action('start', 'localhost', '/bin/true'))
        s1.add_dep(target=s2)
        s2.add_dep(target=s3)
        s2.add_dep(target=s4)
        manager.register_services(s1, s2, s3, s4)
        manager.call_services([], 'start')
        self.assertEqual(s1.status, DONE)
        self.assertEqual(s2.status, DONE)
        self.assertEqual(s3.status, DONE)
        self.assertEqual(s4.status, DONE)

    def test_call_services_case_errors(self):
        '''Test errors generated by call_services'''
        manager = service_manager_self()
        s1 = Service('S1')
        s2 = Service('S2')
        s3 = Service('S3')
        s4 = Service('S4')
        s1.add_action(Action('start', 'localhost', '%TARGET'))
        s2.add_action(Action('start', 'localhost', '/bin/true'))
        s3.add_action(Action('start', 'localhost', '/bin/true'))
        s4.add_action(Action('start', 'localhost', '/bin/true'))
        s1.add_dep(target=s2)
        s2.add_dep(target=s3)
        s2.add_dep(target=s4)
        manager.register_services(s1, s2, s3, s4)
        self.assertRaises(AssertionError,
            manager.call_services, None, None)
        self.assertRaises(ServiceNotFoundError,
            manager.call_services, ['S8'], 'start')
        self.assertRaises(ServiceNotFoundError,
            manager.call_services, ['S2', 'S8'], 'start')
        self.assertRaises(ActionNotFoundError,
            manager.call_services, None, 'stup')
        self.assertRaises(ActionNotFoundError,
            manager.call_services, ['S1'], 'stup')
        self.assertRaises(ActionNotFoundError,
            manager.call_services, ['S3', 'S4'], 'stup')

    def test_excluded_variable_creation(self):
        '''Test creation of the variable excluded wether -x is specified'''
        class MockOptions(object):
            def __init__(self):
                 self.hijack_nodes = NodeSet('epsilon[14-18]')
                 self.config_dir = None
                 self.hijack_servs = None
                 self.only_nodes = None
        manager = service_manager_self()
        manager.call_services(None, 'start', MockOptions())
        self.assertTrue('EXCLUDED_NODES' in manager.variables)
        self.assertEqual(manager.variables['EXCLUDED_NODES'],
                         NodeSet('epsilon[14-18]'))