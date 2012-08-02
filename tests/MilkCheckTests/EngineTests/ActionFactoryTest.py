# Copyright CEA (2011)
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

'''
This modules defines the tests cases targeting ActionFactory
'''
from unittest import TestCase
from ClusterShell.NodeSet import NodeSet
from MilkCheck.Engine.ActionFactory import ActionFactory

class ActionFactoryTest(TestCase):
    '''Test cases applied to ActionFactory'''

    def test_create_action(self):
        '''Test instanciation of an Action'''
        act = ActionFactory.create_action('start', target='localhost')
        self.assertTrue(act)
        self.assertEqual(act.name, 'start')
        self.assertEqual(act.target, NodeSet('localhost'))
        
    def test_create_action_from_dict1(self):
        '''Test instanciation of an Action through a dictionnary'''
        act = ActionFactory.create_action_from_dict(
            {
                'start':
                {
                    'target': 'localhost',
                    'fanout': 4,
                    'retry': 5,
                    'delay': 2,
                    'timeout': 4,
                    'cmd': '/bin/True',
                    'desc': 'my desc',
                }
            }
        )
        self.assertTrue(act)
        self.assertEqual(act.name, 'start')
        self.assertEqual(act.target, NodeSet('localhost'))
        self.assertEqual(act.fanout, 4)
        self.assertEqual(act.retry, 5)
        self.assertEqual(act.delay, 2)
        self.assertEqual(act.timeout, 4)
        self.assertEqual(act.command, '/bin/True')
        self.assertEqual(act.desc, 'my desc')

    def test_create_action_from_dict2(self):
        '''Test instanciation of an action with variables'''
        act = ActionFactory.create_action_from_dict(
            {
                'start':
                {
                    'target': 'localhost',
                    'variables': {
                        'var1': 'toto',
                        'var2': 'titi'
                     },
                    'fanout': 4,
                    'retry': 5,
                    'delay': 2,
                    'timeout': 4,
                    'cmd': '/bin/True'
                }
            }
        )
        self.assertTrue(act)
        self.assertTrue(len(act.variables) == 2)
        self.assertTrue('var1' in act.variables)
        self.assertTrue('var2' in act.variables)
