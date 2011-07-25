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
from MilkCheck.Callback import CallbackHandler
from ClusterShell.NodeSet import NodeSet

# Symbols
from MilkCheck.Engine.BaseEntity import DONE, NO_STATUS, TOO_MANY_ERRORS
from MilkCheck.Engine.BaseEntity import ERROR
from MilkCheck.UI.UserView import RC_OK, RC_WARNING, RC_ERROR, RC_EXCEPTION
from MilkCheck.UI.UserView import RC_UNKNOWN_EXCEPTION

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
        s1.desc = 'I am the service S1'
        s2 = Service('S2')
        s2.desc = 'I am the service S2'
        s3 = Service('S3')
        s3.desc = 'I am the service S3'
        s4 = Service('S4')
        s4.desc = 'I am the service S4'
        g1 = ServiceGroup('G1')
        i1 = Service('I1')
        i1.desc = 'I am the service I1'
        i2 = Service('I2')
        i2.desc = 'I am the service I2'

        # Actions S1
        start_s1 = Action('start', 'localhost, fortoy8', '/bin/true')
        start_s1.delay = 2
        stop_s1 = Action('stop', 'localhost,fortoy8', '/bin/true')
        stop_s1.delay = 2
        s1.add_actions(start_s1, stop_s1)
        # Actions S2
        start_s2 = Action('start', 'localhost,fortoy8', '/bin/true')
        stop_s2 = Action('stop', 'localhost,fortoy8', '/bin/true')
        s2.add_actions(start_s2, stop_s2)
        # Actions S3
        start_s3 = Action('start', 'localhost,fortoy8', '/bin/false')
        stop_s3 = Action('stop', 'localhost,fortoy8', '/bin/false')
        s3.add_actions(start_s3, stop_s3)
        # Actions S4
        start_s4 = Action('start', 'localhost,fortoy8', 'hostname')
        stop_s4 = Action('stop', 'localhost,fortoy8', '/bin/true')
        s4.add_actions(start_s4, stop_s4)
        # Actions I1
        start_i1 = Action('start', 'localhost,fortoy8', '/bin/true')
        stop_i1 = Action('stop', 'localhost,fortoy8', '/bin/true')
        i1.add_actions(start_i1, stop_i1)
        # Actions I2
        start_i2 = Action('start', 'localhost,fortoy8', '/bin/true')
        stop_i2 = Action('stop', 'localhost,fortoy8', '/bin/true')
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

    def tearDown(self):
        CallbackHandler._instance = None

    def test_instanciation_cli(self):
        '''Test the instanciation of the CLI'''
        self.assertTrue(CommandLineInterface())

    def test_execute_service_from_CLI(self):
        '''Execute a service from the CLI'''
        cli = CommandLineInterface()
        retcode = cli.execute(['G1', 'stop', '-vvv', '-x', 'fortoy8'])
        manager = service_manager_self()
        self.assertEqual(manager.entities['S1'].status, DONE)
        self.assertEqual(manager.entities['S3'].status, TOO_MANY_ERRORS)
        self.assertEqual(manager.entities['G1'].status, ERROR)
        self.assertEqual(retcode, RC_ERROR)

    def test_execute_services_verbosity(self):
        '''Test method execute to run services with different verbosity'''
        cli = CommandLineInterface()
        cli.profiling = True
        self.assertEqual(cli.execute(['S3', 'start']), RC_ERROR)
        self.assertTrue(cli.count_low_verbmsg > 0)
        self.assertTrue(cli.count_average_verbmsg == 0)
        self.assertTrue(cli.count_high_verbmsg == 0)
        self.assertEqual(cli.execute(['S3', 'start', '-v']), RC_ERROR)
        self.assertTrue(cli.count_low_verbmsg > 0)
        self.assertTrue(cli.count_average_verbmsg > 0)
        self.assertTrue(cli.count_high_verbmsg == 0)
        self.assertEqual(cli.execute(['S3', 'start', '-vv']), RC_ERROR)
        self.assertTrue(cli.count_low_verbmsg > 0)
        self.assertTrue(cli.count_average_verbmsg > 0)
        self.assertTrue(cli.count_high_verbmsg > 0)
        self.assertEqual(cli.execute(['S3', 'start', '-d']), RC_ERROR)
        self.assertTrue(cli.count_low_verbmsg > 0)
        self.assertTrue(cli.count_average_verbmsg > 0)
        self.assertTrue(cli.count_high_verbmsg > 0)

    def test_execute_services_exclusion(self):
        '''Test exclusion of services from the CLI'''
        cli = CommandLineInterface()
        # Execute start on S1 with verbosity at level one, do not process
        # the node S3 moreover excluded nodes
        cli.profiling = True
        retcode = cli.execute(
            ['S1', 'start', '-vvv', '-X', 'S3', '-x', 'fortoy8'])
        manager = service_manager_self()
        self.assertEqual(retcode, RC_OK)
        self.assertEqual(manager.entities['S1'].status, DONE)
        self.assertEqual(manager.entities['S2'].status, DONE)
        self.assertEqual(manager.entities['S4'].status, NO_STATUS)
        self.assertEqual(manager.entities['G1'].status, NO_STATUS)
        self.assertTrue(cli.count_low_verbmsg > 0)
        self.assertTrue(cli.count_average_verbmsg > 0)
        self.assertTrue(cli.count_high_verbmsg > 0)

    def test_execute_nodes_exclusion(self):
        '''Test nodes exlcusion from the CLI'''
        cli = CommandLineInterface()
        retcode = cli.execute(['S3', 'stop', '-vvv', '-x', 'fortoy8'])
        manager = service_manager_self()
        self.assertEqual(retcode, RC_ERROR)
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
        retcode = cli.execute(['S1', 'start', '-d', '-n', 'localhost'])
        manager = service_manager_self()
        self.assertEqual(retcode, RC_ERROR)
        self.assertEqual(manager.entities['S1'].status, ERROR)
        self.assertEqual(manager.entities['S2'].status, DONE)
        self.assertEqual(manager.entities['S3'].status, TOO_MANY_ERRORS)
        self.assertEqual(manager.entities['S4'].status, DONE)
        self.assertEqual(manager.entities['G1'].status, DONE)
        self.assertTrue(manager.entities['S1']._actions['start'].target  ==\
            NodeSet('localhost'))
        self.assertTrue(manager.entities['S2']._actions['start'].target  ==\
            NodeSet('localhost'))
        self.assertTrue(manager.entities['S3']._actions['start'].target  ==\
            NodeSet('localhost'))
        self.assertTrue(manager.entities['S4']._actions['start'].target  ==\
            NodeSet('localhost'))

    def test_execute_multiple_services(self):
        '''Test execution of S2 and G1 at the same time'''
        cli = CommandLineInterface()
        retcode = cli.execute(['S2', 'G1', 'start', '-d', '-x', 'fortoy8'])
        manager = service_manager_self()
        self.assertEqual(retcode, RC_OK)
        self.assertEqual(manager.entities['S2'].status, DONE)
        self.assertEqual(manager.entities['G1'].status, DONE)

    def test_execute_multiple_services_reverse(self):
        '''Test reverse execution of S2 and G1 at the same time'''
        cli = CommandLineInterface()
        retcode = cli.execute(['S2', 'G1', 'stop', '-d', '-x', 'fortoy8'])
        manager = service_manager_self()
        self.assertEqual(retcode, RC_ERROR)
        self.assertEqual(manager.entities['S1'].status, DONE)
        self.assertEqual(manager.entities['S3'].status, TOO_MANY_ERRORS)
        self.assertEqual(manager.entities['S2'].status, DONE)
        self.assertEqual(manager.entities['G1'].status, ERROR)

    def test_execute_overall_graph(self):
        '''Test no services required so make all'''
        cli = CommandLineInterface()
        retcode = cli.execute(['start', '-d', '-x', 'fortoy8'])
        manager = service_manager_self()
        self.assertEqual(retcode, RC_ERROR)
        self.assertEqual(manager.entities['S1'].status, ERROR)
        self.assertEqual(manager.entities['S2'].status, DONE)
        self.assertEqual(manager.entities['S3'].status, TOO_MANY_ERRORS)
        self.assertEqual(manager.entities['S4'].status, DONE)
        self.assertEqual(manager.entities['G1'].status, DONE)

    def test_execute_overall_graph_reverse(self):
        '''Test no services required so make all reverse'''
        cli = CommandLineInterface()
        retcode = cli.execute(['stop', '-d', '-x', 'fortoy8'])
        manager = service_manager_self()
        self.assertEqual(retcode, RC_ERROR)
        self.assertEqual(manager.entities['S1'].status, DONE)
        self.assertEqual(manager.entities['S2'].status, DONE)
        self.assertEqual(manager.entities['S3'].status, TOO_MANY_ERRORS)
        self.assertEqual(manager.entities['S4'].status, ERROR)
        self.assertEqual(manager.entities['G1'].status, ERROR)

    def test_execute_retcode_exception(self):
       '''
       Test if the method execute returns 9 if a known exception is raised
       '''
       cli = CommandLineInterface()
       self.assertEqual(cli.execute(['stup']), RC_EXCEPTION)
       self.assertEqual(cli.execute(['S6', 'start']), RC_EXCEPTION)

    def test_execute_retcode_unknow_exception(self):
        '''
        Test if the method execute returns 12 if an unknown exception is raised
        '''
        cli = CommandLineInterface()
        self.assertRaises(TypeError, cli.execute, [8, 9])
