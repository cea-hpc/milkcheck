# Copyright CEA (2011)
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This modules defines the tests cases targeting the class CommandLineInterface
"""

# Classes
from unittest import TestCase
from MilkCheck.UI.Cli import CommandLineInterface
from MilkCheck.ServiceManager import ServiceManager
from MilkCheck.ServiceManager import service_manager_self
from MilkCheck.Engine.Service import Service
from MilkCheck.Engine.Action import Action
from MilkCheck.Engine.ServiceGroup import ServiceGroup
from MilkCheck.Engine.BaseEntity import DONE, NO_STATUS, TOO_MANY_ERRORS
from MilkCheck.Engine.BaseEntity import ERROR
from ClusterShell.NodeSet import NodeSet

class CommandLineInterfaceTests(TestCase):
    '''Tests cases of the command line interface'''

    def setUp(self):
        '''
        Set up the graph of services within the service manager
        
        Graphe
                ---> S2
            S1                            --> I1 
                        ---> G1 --> (sour)       --> (sink)
                ---> S3                   --> I2 
                        ---> S4
                        
        Each node has an action start and an action stop
        '''
        ServiceManager._instance = None 
        manager = service_manager_self()
        s1 = Service('S1')
        s2 = Service('S2')
        s3 = Service('S3')
        s4 = Service('S4')
        g1 = ServiceGroup('G1')
        i1 = Service('I1')
        i2 = Service('I2')

        # Actions S1
        start_s1 = Action('start', 'localhost, 127.0.0.1', '/bin/true')
        stop_s1 = Action('stop', 'localhost,127.0.0.1', '/bin/true')
        s1.add_actions(start_s1, stop_s1)
        # Actions S2
        start_s2 = Action('start', 'localhost,127.0.0.1', '/bin/true')
        stop_s2 = Action('stop', 'localhost,127.0.0.1', '/bin/true')
        s2.add_actions(start_s2, stop_s2)
        # Actions S3
        start_s3 = Action('start', 'localhost,127.0.0.1', '/bin/false')
        stop_s3 = Action('stop', 'localhost, 127.0.0.1', '/bin/false')
        s3.add_actions(start_s3, stop_s3)
        # Actions S4
        start_s4 = Action('start', 'localhost,127.0.0.1', '/bin/true')
        stop_s4 = Action('stop', 'localhost,127.0.0.1', '/bin/true')
        s4.add_actions(start_s4, stop_s4)
        # Actions I1
        start_i1 = Action('start', 'localhost,127.0.0.1', '/bin/true')
        stop_i1 = Action('stop', 'localhost,127.0.0.1', '/bin/true')
        i1.add_actions(start_i1, stop_i1)
        # Actions I2
        start_i2 = Action('start', 'localhost,127.0.0.1', '/bin/true')
        stop_i2 = Action('stop', 'localhost,127.0.0.1', '/bin/true')
        i2.add_actions(start_i2, stop_i2)

        # Build graph
        s1.add_dep(target=s2)
        s1.add_dep(target=s3)
        s3.add_dep(target=g1)
        s3.add_dep(target=s4)
        g1.add_inter_dep(target=i1)
        g1.add_inter_dep(target=i2)

        # Register services within the manager
        manager.register_services(s1, s2, s3, s4, g1)

    def test_instanciation_cli(self):
        '''Test the instanciation of the CLI'''
        self.assertTrue(CommandLineInterface())

    def test_execute_services_verbosity(self):
        '''Test method execute to run services with different verbosity'''
        cli = CommandLineInterface()
        cli.profiling = True
        cli.execute(['S3', 'start', '-v'])
        self.assertTrue(cli.count_low_verbmsg > 0)
        self.assertTrue(cli.count_average_verbmsg == 0)
        self.assertTrue(cli.count_high_verbmsg == 0)
        cli.execute(['S3', 'start', '-vv'])
        self.assertTrue(cli.count_low_verbmsg > 0)
        self.assertTrue(cli.count_average_verbmsg > 0)
        self.assertTrue(cli.count_high_verbmsg == 0)
        cli.execute(['S3', 'start', '-vvv'])
        self.assertTrue(cli.count_low_verbmsg > 0)
        self.assertTrue(cli.count_average_verbmsg > 0)
        self.assertTrue(cli.count_high_verbmsg > 0)
        cli.execute(['S3', 'start', '-d'])
        self.assertTrue(cli.count_low_verbmsg > 0)
        self.assertTrue(cli.count_average_verbmsg > 0)
        self.assertTrue(cli.count_high_verbmsg > 0)

    def test_execute_services_exclusion(self):
        '''Test exclusion of services from the CLI'''
        cli = CommandLineInterface()
        # Execute start on S1 with verbosity at level one, do not process
        # the node S3 moreover hijack cluster nodes aury11 and aury12
        cli.profiling = True
        cli.execute(['S1', 'start', '-v', '-X', 'S3'])
        manager = service_manager_self()
        self.assertEqual(manager.entities['S1'].status, DONE)
        self.assertEqual(manager.entities['S2'].status, DONE)
        self.assertEqual(manager.entities['S4'].status, NO_STATUS)
        self.assertEqual(manager.entities['G1'].status, NO_STATUS)
        self.assertTrue(cli.count_low_verbmsg > 0)
        self.assertTrue(cli.count_average_verbmsg == 0)
        self.assertTrue(cli.count_high_verbmsg == 0)

    def test_execute_nodes_exlcusion(self):
        '''Test nodes exlcusion from the CLI'''
        cli = CommandLineInterface()
        cli.execute(['S3', 'stop', '-vvv', '-x', '127.0.0.1'])
        manager = service_manager_self()
        self.assertEqual(manager.entities['S2'].status, NO_STATUS)
        self.assertEqual(manager.entities['S4'].status, NO_STATUS)
        self.assertEqual(manager.entities['G1'].status, NO_STATUS)
        self.assertEqual(manager.entities['S1'].status, DONE)
        self.assertEqual(manager.entities['S3'].status, TOO_MANY_ERRORS)
        self.assertTrue(manager.entities['S1']._actions['stop'].target  ==\
            NodeSet('localhost'))
        self.assertTrue(manager.entities['S3']._actions['stop'].target  ==\
            NodeSet('localhost'))

    def test_execute_nodes_only(self):
        '''Test mandatory nodes from CLI'''
        cli = CommandLineInterface()
        cli.execute(['S1', 'start', '-d', '-n', '127.0.0.1'])
        manager = service_manager_self()
        self.assertEqual(manager.entities['S1'].status, ERROR)
        self.assertEqual(manager.entities['S2'].status, DONE)
        self.assertEqual(manager.entities['S3'].status, TOO_MANY_ERRORS)
        self.assertEqual(manager.entities['S4'].status, DONE)
        self.assertEqual(manager.entities['G1'].status, DONE)
        self.assertTrue(manager.entities['S1']._actions['start'].target  ==\
            NodeSet('127.0.0.1'))
        self.assertTrue(manager.entities['S2']._actions['start'].target  ==\
            NodeSet('127.0.0.1'))
        self.assertTrue(manager.entities['S3']._actions['start'].target  ==\
            NodeSet('127.0.0.1'))
        self.assertTrue(manager.entities['S4']._actions['start'].target  ==\
            NodeSet('127.0.0.1'))