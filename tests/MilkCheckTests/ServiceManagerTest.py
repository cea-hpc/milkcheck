# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

'''
This modules defines the tests cases targeting the internal class
RunningTasksManager and the ServiceManager itself
'''

# Classes
import socket
from unittest import TestCase
from ClusterShell.NodeSet import NodeSet
from MilkCheck.Engine.Service import Service, ActionNotFoundError
from MilkCheck.Engine.Action import Action
from MilkCheck.ServiceManager import ServiceManager, service_manager_self
from MilkCheck.ServiceManager import ServiceAlreadyReferencedError
from MilkCheck.ServiceManager import ServiceNotFoundError

# Symbols
from MilkCheck.Engine.BaseEntity import NO_STATUS, DONE, REQUIRE_WEAK
from MilkCheck.UI.UserView import RC_OK, RC_WARNING, RC_ERROR

HOSTNAME = socket.gethostname().split('.')[0]

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
        s1.add_action(Action('start', HOSTNAME, '/bin/true'))
        s2.add_action(Action('start', HOSTNAME, '/bin/true'))
        s3.add_action(Action('start', HOSTNAME, '/bin/true'))
        s4.add_action(Action('start', HOSTNAME, '/bin/true'))
        s1.add_dep(target=s2)
        s2.add_dep(target=s3)
        s2.add_dep(target=s4)
        manager.register_services(s1, s2, s3, s4)
        retcode = manager.call_services(['S2'], 'start')
        self.assertEqual(retcode, RC_OK)
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
        s1.add_action(Action('start', HOSTNAME, '/bin/true'))
        s2.add_action(Action('start', HOSTNAME, '/bin/true'))
        s3.add_action(Action('start', HOSTNAME, '/bin/true'))
        s4.add_action(Action('start', HOSTNAME, '/bin/true'))
        s1.add_dep(target=s2)
        s2.add_dep(target=s3)
        s2.add_dep(target=s4)
        manager.register_services(s1, s2, s3, s4)
        retcode = manager.call_services(['S3','S4'], 'start')
        self.assertEqual(retcode, RC_OK)
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
        s1.add_action(Action('start', HOSTNAME, '/bin/true'))
        s2.add_action(Action('start', HOSTNAME, '/bin/true'))
        s3.add_action(Action('start', HOSTNAME, '/bin/true'))
        s4.add_action(Action('start', HOSTNAME, '/bin/true'))
        s1.add_dep(target=s2)
        s2.add_dep(target=s3)
        s2.add_dep(target=s4)
        manager.register_services(s1, s2, s3, s4)
        retcode = manager.call_services([], 'start')
        self.assertEqual(retcode, RC_OK)
        self.assertEqual(s1.status, DONE)
        self.assertEqual(s2.status, DONE)
        self.assertEqual(s3.status, DONE)
        self.assertEqual(s4.status, DONE)

    def test_call_services_retcode0(self):
        '''Test call_services return 0 whether source is DONE'''
        manager = service_manager_self()
        s1 = Service('S1')
        s2 = Service('S2')
        s3 = Service('S3')
        s4 = Service('S4')
        s1.add_action(Action('start', HOSTNAME, '/bin/true'))
        s2.add_action(Action('start', HOSTNAME, '/bin/true'))
        s3.add_action(Action('start', HOSTNAME, '/bin/true'))
        s4.add_action(Action('start', HOSTNAME, '/bin/true'))
        s1.add_dep(target=s2)
        s2.add_dep(target=s3)
        s2.add_dep(target=s4)
        manager.register_services(s1, s2, s3, s4)
        self.assertEqual(manager.call_services([], 'start'), RC_OK)

    def test_call_services_retcode3(self):
        '''Test call_services return 3 whether source is WARNING'''
        manager = service_manager_self()
        s1 = Service('S1')
        s2 = Service('S2')
        s3 = Service('S3')
        s4 = Service('S4')
        s1.add_action(Action('start', HOSTNAME, '/bin/true'))
        s2.add_action(Action('start', HOSTNAME, '/bin/false'))
        s3.add_action(Action('start', HOSTNAME, '/bin/true'))
        s4.add_action(Action('start', HOSTNAME, '/bin/true'))
        s1.add_dep(target=s2, sgth=REQUIRE_WEAK)
        s2.add_dep(target=s3)
        s2.add_dep(target=s4)
        manager.register_services(s1, s2, s3, s4)
        self.assertEqual(manager.call_services([], 'start'), RC_WARNING)

    def test_call_services_retcode6(self):
        '''Test call_services return 6 whether source is DEP_ERROR'''
        manager = service_manager_self()
        s1 = Service('S1')
        s2 = Service('S2')
        s3 = Service('S3')
        s4 = Service('S4')
        s1.add_action(Action('start', HOSTNAME, '/bin/true'))
        s2.add_action(Action('start', HOSTNAME, '/bin/false'))
        s3.add_action(Action('start', HOSTNAME, '/bin/true'))
        s4.add_action(Action('start', HOSTNAME, '/bin/true'))
        s1.add_dep(target=s2)
        s2.add_dep(target=s3)
        s2.add_dep(target=s4)
        manager.register_services(s1, s2, s3, s4)
        self.assertEqual(manager.call_services([], 'start'), RC_ERROR)

    def test_call_services_case_errors(self):
        '''Test errors generated by call_services'''
        manager = service_manager_self()
        s1 = Service('S1')
        s2 = Service('S2')
        s3 = Service('S3')
        s4 = Service('S4')
        s1.add_action(Action('start', HOSTNAME, '%TARGET'))
        s2.add_action(Action('start', HOSTNAME, '/bin/true'))
        s3.add_action(Action('start', HOSTNAME, '/bin/true'))
        s4.add_action(Action('start', HOSTNAME, '/bin/true'))
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
