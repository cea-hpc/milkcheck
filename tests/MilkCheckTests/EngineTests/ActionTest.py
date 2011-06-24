# Copyright CEA (2011)
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This modules defines the tests cases targeting the BaseService
"""

# Classes
from re import findall, search
from unittest import TestCase
from MilkCheck.Engine.Action import Action, NodeInfo
from MilkCheck.Engine.Service import Service
from ClusterShell.NodeSet import NodeSet

# Exceptions
from MilkCheck.Engine.Action import UndefinedVariableError

# Symbols
from MilkCheck.Engine.BaseEntity import NO_STATUS, DONE, TIMED_OUT, ERROR
from MilkCheck.Engine.BaseEntity import TOO_MANY_ERRORS, WAITING_STATUS
from MilkCheck.Engine.BaseEntity import DONE_WITH_WARNINGS 

class NodeInfoTest(TestCase):
    '''Define tests cases for the object NodeInfo'''

    class MockWorker(object):
            '''Mock the behaviour of a worker object'''
            def __init__(self):
                self.command = 'hostname'

            def last_read(self):
                '''Return tuple of (node, buffer)'''
                return ('localhost', '127.0.0.1')

            def last_retcode(self):
                '''Return tuple of (node, exit_code)'''
                return ('localhost', 0)
                
    def test_instanciation(self):
        '''Test instanciation of a NodeInfo'''
        cnode = NodeInfo(node='localhost', command='tree')
        self.assertTrue(cnode)
        self.assertEqual(cnode.node, 'localhost')
        self.assertEqual(cnode.command, 'tree')

    def test_instanciation_from_worker(self):
        '''Test instanciation of a NodeInfo from a worker'''
        cnode = NodeInfo.from_worker(NodeInfoTest.MockWorker())
        self.assertTrue(cnode)
        self.assertEqual(cnode.node, 'localhost')
        self.assertEqual(cnode.command, 'hostname')
        self.assertEqual(cnode.node_buffer, '127.0.0.1')
        self.assertEqual(cnode.exit_code, 0)
        
class ActionTest(TestCase):
    """Define the unit tests for the object action."""

    def test_action_instanciation(self):
        """Test instanciation of an action."""
        action = Action('start')
        self.assertNotEqual(action, None, 'should be none')
        self.assertEqual(action.name, 'start', 'wrong name')
        action = Action(name='start', target='fortoy5', command='/bin/true')
        self.assertEqual(action.target, NodeSet('fortoy5'), 'wrong target')
        self.assertEqual(action.command, '/bin/true', 'wrong command')
        action = Action(name='start', target='fortoy5', command='/bin/true',
                    timeout=10, delay=5)
        self.assertEqual(action.timeout, 10, 'wrong timeout')
        self.assertEqual(action.delay, 5, 'wrong delay')

    def test_reset_action(self):
        '''Test resest values of an action'''
        action = Action(name='start', target='fortoy5', command='/bin/true',
                    timeout=10, delay=5)
        action.retry = 4
        action._retry_backup = 5
        action.worker = 'test'
        action.start_time = '00:20:30'
        action.stop_time = '00:20:30'
        action.reset()
        self.assertEqual(action.retry, 5)
        self.assertEqual(action.worker, None)
        self.assertEqual(action.start_time, None)
        self.assertEqual(action.stop_time, None)
        self.assertEqual(action.status, NO_STATUS)

    def test_has_too_many_errors(self):
        """Test the method has_too_many_errors."""
        action = Action(name='start', target='aury[12,13,21]',
                    command='/bin/false')
        action.errors = 2
        service = Service('test_service')
        service.add_action(action)
        service.run('start')
        last_action = service.last_action()
        self.assertTrue(last_action.has_too_many_errors())

        act_test = Action(name='test', target='fortoy5', command='/bin/true')
        service.add_action(act_test)
        service.run('test')
        last_action = service.last_action()
        self.assertFalse(last_action.has_too_many_errors())

    def test_has_timed_out(self):
        """Test has_timed_out_method."""
        action = Action(name='start', target='localhost',
                    command='sleep 3', timeout=2)
        service = Service('test_service')
        service.add_action(action)
        service.run('start')
        last_action = service.last_action()
        self.assertTrue(last_action.has_timed_out())

    def test_set_retry(self):
        """Test retry assignement"""
        action =  Action(name='start', target='localhost', command='sleep 3')
        self.assertRaises(AssertionError, action.set_retry, 5)
        action =  Action(name='start', target='localhost', command='sleep 3',
                    delay=3)
        action.retry = 5
        self.assertEqual(action.retry, 5)

    def test_schedule(self):
        """Test behaviour method schedule"""
        a1 = Action(name='start', target='localhost', command='/bin/true')
        a2 = Action(name='status', target='localhost',
                    command='/bin/true', delay=3)
        ser = Service('TEST')
        ser.add_actions(a1, a2)
        a1.run()
        a2.run()
        self.assertTrue(0 < a1.duration and a1.duration < 0.5)
        self.assertTrue(2.8 < a2.duration and a2.duration < 3.5)

    def test_prepare_dep_success(self):
        """Test prepare an action with a single successful dependency"""
        a1 = Action('start', 'localhost', '/bin/true')
        a2 = Action('status', 'localhost', '/bin/true')
        ser = Service('TEST')
        a1.add_dep(a2)
        ser.add_actions(a1, a2)
        a1.run()
        self.assertEqual(a1.status, DONE)
        self.assertFalse(a1.duration)
        self.assertEqual(a2.status, DONE)
        self.assertTrue(a2.duration)

    def test_prepare_dep_failed(self):
        """Test prepare an action with a single failed dependency"""
        a1 = Action('start', 'localhost', '/bin/true')
        a2 = Action('status', 'localhost', '/bin/false')
        ser = Service('TEST')
        a1.add_dep(a2)
        ser.add_actions(a1, a2)
        a1.run()
        self.assertEqual(a1.status, DONE)
        self.assertTrue(a1.duration)
        self.assertEqual(a2.status, TOO_MANY_ERRORS)
        self.assertTrue(a2.duration)

    def test_prepare_actions_graph(self):
        """Test prepare an action graph without errors"""
        a1 = Action('start', 'localhost', '/bin/true')
        a2 = Action('start_engine', 'localhost', '/bin/true')
        a3 = Action('start_gui', 'localhost', '/bin/true')
        a4 = Action('empty_home', 'localhost', '/bin/true')
        a1.add_dep(a2)
        a1.add_dep(a3)
        a2.add_dep(a4)
        a3.add_dep(a4)
        ser = Service('TEST')
        ser.add_actions(a1, a2, a3, a4)
        a1.run()
        self.assertEqual(a1.status, DONE)
        self.assertFalse(a1.duration)
        self.assertEqual(a2.status, DONE)
        self.assertFalse(a2.duration)
        self.assertEqual(a3.status, DONE)
        self.assertFalse(a3.duration)
        self.assertEqual(a4.status, DONE)
        self.assertTrue(a4.duration)

    def test_prepare_actions_graph_with_errors(self):
        """Test prepare an action graph with errors"""
        a1 = Action('start', 'localhost', '/bin/true')
        a2 = Action('start_engine', 'localhost', '/bin/true')
        a3 = Action('start_gui', 'localhost', '/bin/false')
        a4 = Action('empty_home', 'localhost', '/bin/false')
        a1.add_dep(a2)
        a1.add_dep(a3)
        a2.add_dep(a4)
        a3.add_dep(a4)
        ser = Service('TEST')
        ser.add_actions(a1, a2, a3, a4)
        a1.run()
        self.assertEqual(a1.status, DONE)
        self.assertTrue(a1.duration)
        self.assertEqual(a2.status, DONE)
        self.assertTrue(a2.duration)
        self.assertEqual(a3.status, TOO_MANY_ERRORS)
        self.assertTrue(a3.duration)
        self.assertEqual(a4.status, TOO_MANY_ERRORS)
        self.assertTrue(a4.duration)

    def test_command_resolution1(self):
        """Test variable replacement within the action's command 1"""
        a1 = Action('start', 'localhost')
        a1.command = '$HOSTS_SSH service user_access status'
        self.assertRaises(UndefinedVariableError, a1.resolved_command)

    def test_command_resolution2(self):
        """Test variable replacement within the action's command 2"""
        a1 = Action('start', 'localhost')
        a1.command = '$HOSTS_SSH service user_access status'
        a1.add_var('HOSTS_SSH', 'fortoy1,fortoy2')
        fingerprints = findall('fortoy1,fortoy2', a1.resolved_command())
        self.assertTrue(len(fingerprints) == 1)

    def test_command_resolution3(self):
        """Test variable replacement within the action's command 3"""
        a1 = Action('start', 'localhost')
        a1.command = '$HOSTS_SSH service user_access status'
        ser = Service('TEST')
        ser.add_var('HOSTS_SSH', 'fortoy1,fortoy2')
        a1.service = ser
        fingerprints = findall('fortoy1,fortoy2', a1.resolved_command())
        self.assertTrue(len(fingerprints) == 1)

    def test_command_resolution4(self):
        '''Test variable replacement within the action's command 4'''
        a1 = Action('start', 'localhost')
        a1.command = '$TARGET service $SNAME $NAME'
        ser = Service('TEST')
        a1.service = ser
        ser = Service('TEST')
        ser.add_var('SNAME', 'user_access')
        a1.service = ser
        cmd = a1.resolved_command()
        self.assertTrue(search('localhost', cmd))
        self.assertTrue(search('user_access', cmd))
        self.assertTrue(search('start', cmd))

    def test_command_resolution_fake(self):
        '''edfefe'''
        a1 = Action('start', 'localhost')
        a1.command = '/bin/true'
        print a1.resolved_command()