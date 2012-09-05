# Copyright CEA (2011)
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

'''
This modules defines the tests cases targeting ServiceFactory and
ServiceGroupFactory.
'''

from unittest import TestCase
from ClusterShell.NodeSet import NodeSet
from MilkCheck.Engine.ServiceGroup import ServiceGroup
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

    def test_service_with_actions_with_one_decl(self):
        """create a service with two actions with comma declaration"""

        svc = ServiceFactory.create_service_from_dict(
            {'service':
                {
                    'name': 'foo',
                    'actions':
                    {
                        'start,stop':
                        {
                            'cmd': 'service foo %ACTION'
                        },
                    }
                }
            }
        )
        self.assertTrue(svc)
        self.assertEqual(len(svc._actions), 2)
        self.assertTrue('start' in svc._actions)
        self.assertTrue('stop' in svc._actions)
        self.assertEqual(svc._actions['start'].command,
                         'service foo %ACTION')
        self.assertEqual(svc._actions['stop'].command,
                         'service foo %ACTION')

    def test_service_with_nodeset_like_actions_with_one_decl(self):
        """create a service with two actions with nodeset-like declaration"""

        svc = ServiceFactory.create_service_from_dict(
            {'service':
                {
                    'name': 'foo',
                    'actions':
                    {
                        'foo[1-2]':
                        {
                            'cmd': 'service foo %ACTION'
                        },
                    }
                }
            }
        )
        self.assertTrue(svc)
        self.assertEqual(len(svc._actions), 2)
        self.assertTrue('foo1' in svc._actions)
        self.assertTrue('foo2' in svc._actions)
        self.assertEqual(svc._actions['foo1'].command,
                         'service foo %ACTION')
        self.assertEqual(svc._actions['foo2'].command,
                         'service foo %ACTION')

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

    def test_create_service_imbrications(self):
        '''Test create service with mutliple level of subservices'''
        sergrp = ServiceGroupFactory.create_servicegroup_from_dict(
        {'service':
            {'services':
                {'svcA':
                    {'require': ['subgroup'],
                    'actions':
                        {'start': {'cmd': '/bin/True'},
                        'stop': {'cmd': '/bin/False'}},
                        'desc': 'I am the subservice $NAME'},
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
            'desc': 'I am a group',
            'target': 'localhost',
            'name': 'groupinit'}})
        for subservice in ('svcA', 'subgroup'):
            if isinstance(sergrp._subservices[subservice], ServiceGroup):
                for subsubser in ('svcB', 'svcC'):
                    self.assertTrue(
                    sergrp._subservices[subservice].has_subservice(subsubser))
            self.assertTrue(sergrp.has_subservice(subservice))

    def test_inheritance(self):
        '''Test properties inherited from ServiceGroup to Service and Action'''
        sergrp = ServiceGroupFactory.create_servicegroup_from_dict(
        {'service':
            {'services':
                {'svcA':
                    {'require': ['subgroup'],
                    'actions':
                        {'start': {'cmd': '/bin/True'},
                        'stop': {'cmd': '/bin/False'}},
                        'desc': 'I am the subservice $NAME'},
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
            'desc': 'I am a group',
            'target': 'localhost',
            'name': 'groupinit'}})
        self.assertEqual(
            sergrp._subservices['svcA'].target, NodeSet('localhost'))
        self.assertEqual(
            sergrp._subservices['subgroup'].target, NodeSet('127.0.0.1'))
        subgroup = sergrp._subservices['subgroup']
        self.assertEqual(
            subgroup._subservices['svcB'].target, NodeSet('127.0.0.1'))
        self.assertEqual(
            subgroup._subservices['svcC'].target, NodeSet('127.0.0.1'))

    def test_servicegroup_with_nodeset_like_actions_with_one_decl(self):
        '''Test a service group with several group with nodeset-like names'''
        sergrp = ServiceGroupFactory.create_servicegroup_from_dict(
            {'service': {
                'name': 'group1',
                'services': {
                    'da[1-3]': {
                        'actions': {'start': {'cmd': '/bin/True'}}
                    },
                },
            } })

        self.assertEqual(len(sergrp._subservices), 3)
        self.assertTrue(sergrp.has_subservice('da1'))
        self.assertTrue(sergrp.has_subservice('da2'))
        self.assertTrue(sergrp.has_subservice('da3'))
        self.assertEqual(len(sergrp._subservices['da1']._actions), 1)
        self.assertEqual(len(sergrp._subservices['da2']._actions), 1)
        self.assertEqual(len(sergrp._subservices['da3']._actions), 1)

    def test_subservices_with_different_actions(self):
        '''Test a service group with subservices with different actions'''
        sergrp = ServiceGroupFactory.create_servicegroup_from_dict(
            {'service': {
                'name': 'group1',
                'services': {
                    'svc1': {
                        'actions': {
                              'start': {'cmd': '/bin/True'},
                              'status': {'cmd': '/bin/True'},
                              'stop': {'cmd': '/bin/True'},
                        }
                    },
                    'svc2': {
                        'require': [ 'svc1' ],
                        'actions': {
                              'start': {'cmd': '/bin/True'},
                              'stop': {'cmd': '/bin/True'},
                              'status': {'cmd': '/bin/True'},
                        }
                    },
                    'svc3': {
                        'require': [ 'svc1' ],
                        'actions': {
                              'start': {'cmd': '/bin/True'},
                              'stop': {'cmd': '/bin/True'},
                              'status': {'cmd': '/bin/True'},
                        }
                    },
                },
            } })

        self.assertEqual(len(sergrp._subservices), 3)
        self.assertTrue(sergrp.has_subservice('svc1'))
        self.assertTrue(sergrp.has_subservice('svc2'))
        self.assertTrue(sergrp.has_subservice('svc3'))
        self.assertEqual(len(sergrp._subservices['svc1']._actions), 3)
        self.assertEqual(len(sergrp._subservices['svc2']._actions), 3)
        self.assertEqual(len(sergrp._subservices['svc3']._actions), 3)
