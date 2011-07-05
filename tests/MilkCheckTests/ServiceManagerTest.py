# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

'''
This modules defines the tests cases targeting the internal class
RunningTasksManager and the ServiceManager itself
'''

# Classes
from unittest import TestCase
from MilkCheck.Engine.Service import Service
from MilkCheck.Engine.Action import Action
from MilkCheck.ServiceManager import ServiceManager, service_manager_self
from MilkCheck.ServiceManager import ServiceAlreadyReferencedError
from MilkCheck.ServiceManager import ServiceNotFoundError

# Symbols
from MilkCheck.Engine.BaseEntity import DONE

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

    def test_call_services(self):
        '''Test behaviour of the method call services'''
        manager = service_manager_self()
        s1 = Service('S1')
        s2 = Service('S2')
        s3 = Service('S3')
        s4 = Service('S4')
        s1.add_action(Action('start', 'localhost', '/bin/true'))
        s1.add_action(Action('stop', 'localhost', '/bin/true'))
        s2.add_action(Action('start', 'localhost', '/bin/true'))
        s2.add_action(Action('stop', 'localhost', '/bin/true'))
        s3.add_action(Action('start', 'localhost', '/bin/true'))
        s3.add_action(Action('stop', 'localhost', '/bin/true'))
        s4.add_action(Action('start', 'localhost', '/bin/true'))
        s4.add_action(Action('stop', 'localhost', '/bin/true'))
        s1.add_dep(target=s2)
        s2.add_dep(target=s3)
        s2.add_dep(target=s4)
        manager.register_services(s1, s2, s3, s4)
        self.assertRaises(AssertionError, manager.call_services, [], 'stop')
        self.assertRaises(AssertionError, manager.call_services,
            ['S1'], None)
        self.assertRaises(ServiceNotFoundError, manager.call_services,
            ['robinhood'], 'start')
        manager.call_services(['S1'], 'start')
        self.assertEqual(s1.status, DONE)
        self.assertEqual(s2.status, DONE)
        self.assertEqual(s3.status, DONE)
        self.assertEqual(s4.status, DONE)
