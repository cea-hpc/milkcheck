# Copyright CEA (2011)
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

'''
This modules defines the tests cases targeting ServiceFactory and
ServiceGroupFactory.
'''

from unittest import TestCase
from ClusterShell.NodeSet import NodeSet
from MilkCheck.Engine.ServiceFactory import ServiceFactory
from MilkCheck.Engine.ServiceFactory import ServiceGroupFactory

class ServiceFactoryTest(TestCase):
    '''This class define the test cases of ServiceFactory'''

    def test_create_minimal_service(self):
        '''Test instanciation of a minimal service'''
        ser = ServiceFactory.create_service('alpha', target='localhost')
        self.assertTrue(ser)
        self.assertEqual(ser.name, 'alpha')
        self.assertEqual(ser.target, NodeSet('localhost'))

    def test_create_service(self):
        '''Test instanciation of a complete service'''
        ser = ServiceFactory.create_service('alpha', desc='fake service',
            target='localhost', fanout=2, origin=True)
        self.assertTrue(ser)
        self.assertEqual(ser.name, 'alpha')
        self.assertEqual(ser.desc, 'fake service')
        self.assertEqual(ser.fanout, 2)
        self.assertTrue(ser.origin)
        self.assertFalse(ser.simulate)
        self.assertEqual(ser.target, NodeSet('localhost'))

    def test_create_service_from_dict1(self):
        '''Test instanciate a service from a dictionnary'''
        ser = ServiceFactory.create_service_from_dict(
            {'service':
                {
                    'name': 'S1',
                    'desc': 'I am the service S1',
                    'target': 'localhost',
                    'variables':{
                        'var1': 'toto',
                        'var2': 'titi'
                    },
                    'actions':
                    {
                        'start': {'cmd': '/bin/True'},
                        'stop': {'cmd': '/bin/True'}
                    }
                }
            }
        )
        self.assertTrue(ser)
        self.assertEqual(ser.name, 'S1')
        self.assertEqual(ser.desc, 'I am the service S1')
        self.assertEqual(ser.target, NodeSet('localhost'))
        self.assertEqual(len(ser.variables), 2)
        self.assertTrue('var1' in ser.variables)
        self.assertTrue('var2' in ser.variables)

    def test_create_service_from_dict2(self):
        '''
        Test instanciate a service from a dictionnary with dependant actions
        '''
        ser = ServiceFactory.create_service_from_dict(
            {'service':
                {
                    'name': 'S1',
                    'desc': 'I am the service S1',
                    'target': 'localhost',
                    'actions':
                    {
                        'start':
                        {
                            'check': ['status'],
                            'cmd': '/bin/True'
                        },
                        'stop': {'cmd': '/bin/True'},
                        'status': {'cmd': '/bin/True'}
                    }
                }
            }
        )
        self.assertTrue(ser)
        self.assertEqual(len(ser._actions), 3)
        self.assertTrue('start' in ser._actions)
        self.assertTrue('stop' in ser._actions)
        self.assertTrue('status' in ser._actions)
        self.assertTrue(ser._actions['start'].has_parent_dep('status'))

class ServiceGroupFactoryTest(TestCase):
    '''Test cases of the class ServiceGroup'''

    def test_create_servicegrp_from_dict1(self):
        '''Test instanciation of a service group from a dictionnary'''
        sergrp = ServiceGroupFactory.create_servicegroup_from_dict(
           {'service':
                {'services':
                    {'hpss_nfs':
                        {'target': 'localhost',
                         'actions':
                            {'start': {'cmd': '/bin/True'},
                            'stop': {'cmd': '/bin/False'}},
                            'desc': "I'm the service hpss_nfs"
                         },
                     'lustre':
                         {'target': 'localhost',
                          'actions':
                            {'start': {'cmd':'/bin/True'},
                             'stop': {'cmd': '/bin/False'}},
                          'desc': "I'm the service lustre"}},
            'variables':{'LUSTRE_FS_LIST': 'store0,work0'},
            'desc': "I'm the service S1",
            'target': 'localhost',
            'variables':{
                'var1': 'toto',
                'var2': 'titi'
            },
            'name': 'S1'}})

        self.assertEqual(len(sergrp.variables), 2)
        self.assertTrue('var1' in sergrp.variables)
        self.assertTrue('var2' in sergrp.variables)
        self.assertTrue(sergrp.has_subservice('hpss_nfs'))
        self.assertTrue(sergrp.has_subservice('lustre'))
        self.assertTrue(
            sergrp._subservices['hpss_nfs'].has_parent_dep('sink'))
        self.assertTrue(
            sergrp._subservices['hpss_nfs'].has_child_dep('source'))
        self.assertTrue(
            sergrp._subservices['lustre'].has_parent_dep('sink'))
        self.assertTrue(
            sergrp._subservices['lustre'].has_child_dep('source'))

    def test_create_servicegrp_from_dict2(self):
        '''
        Test instanciation of a service group with dependencies between
        subservices.
        '''
        sergrp = ServiceGroupFactory.create_servicegroup_from_dict(
           {'service':
                {'services':
                    {'hpss_nfs':
                        {'target': 'localhost',
                         'require': ['lustre', 'test'],
                         'actions':
                            {'start': {'cmd': '/bin/True'},
                            'stop': {'cmd': '/bin/False'}},
                            'desc': "I'm the service hpss_nfs"
                         },
                     'lustre':
                         {'target': 'localhost',
                          'actions':
                            {'start': {'cmd':'/bin/True'},
                             'stop': {'cmd': '/bin/False'}},
                          'desc': "I'm the service lustre"},
                    'test':
                         {'target': 'localhost',
                          'actions':
                            {'start': {'cmd':'/bin/True'},
                             'stop': {'cmd': '/bin/False'}},
                          'desc': "I'm a test suite"}},
            'variables':{'LUSTRE_FS_LIST': 'store0,work0'},
            'desc': "I'm the service S1",
            'target': 'localhost',
            'name': 'S1'}})
        self.assertTrue(sergrp.has_subservice('hpss_nfs'))
        self.assertTrue(sergrp.has_subservice('lustre'))
        self.assertTrue(sergrp.has_subservice('test'))
        self.assertFalse(
            sergrp._subservices['hpss_nfs'].has_parent_dep('sink'))
        self.assertTrue(
            sergrp._subservices['hpss_nfs'].has_child_dep('source'))
        self.assertTrue(
            sergrp._subservices['lustre'].has_parent_dep('sink'))
        self.assertFalse(
            sergrp._subservices['test'].has_child_dep('source'))
        self.assertTrue(
            sergrp._subservices['test'].has_parent_dep('sink'))