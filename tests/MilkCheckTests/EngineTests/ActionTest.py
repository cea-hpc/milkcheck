# Copyright CEA (2011)
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This modules defines the tests cases targeting the BaseService
"""

# Classes
import socket
from re import findall, search
from unittest import TestCase
from MilkCheck.Engine.Action import Action
from MilkCheck.Engine.Service import Service
from ClusterShell.NodeSet import NodeSet

# Symbols
from MilkCheck.Engine.BaseEntity import NO_STATUS, DONE, TIMED_OUT, DEP_ERROR
from MilkCheck.Engine.BaseEntity import ERROR, WAITING_STATUS
from MilkCheck.Engine.BaseEntity import WARNING 

HOSTNAME = socket.gethostname().split('.')[0]

class ActionTest(TestCase):
    """Define the unit tests for the object action."""

    def test_desc(self):
        """Test action inherits 'desc'"""
        # No service description, no action description
        action1 = Action('status', HOSTNAME, '/bin/true')
        service = Service('TEST')
        service.add_actions(action1)
        self.assertEqual(action1.desc, "")

        # Service description, actions inherits the description
        action2 = Action('status', HOSTNAME, '/bin/true')
        service2 = Service('TEST2')
        service2.desc = "Service TEST"
        service2.add_actions(action2)
        action2.inherits_from(service2)
        self.assertEqual(action2.desc, "Service TEST")

    def test_action_instanciation(self):
        """Test instanciation of an action."""
        action = Action('start')
        self.assertNotEqual(action, None)
        self.assertEqual(action.name, 'start')
        action = Action(name='start', target='fortoy5', command='/bin/true')
        self.assertEqual(action.target, NodeSet('fortoy5'))
        self.assertEqual(action.command, '/bin/true')
        action = Action(name='start', target='fortoy5', command='/bin/true',
                    timeout=10, delay=5)
        self.assertEqual(action.timeout, 10)
        self.assertEqual(action.delay, 5)

    def test_local_variables(self):
        '''Test Action local variables'''
        action = Action('bar')
        self.assertEqual(action._resolve("I'm %ACTION"), "I'm bar")

        svc = Service('foo')
        svc.add_action(action)
        self.assertEqual(action._resolve("I'm %SERVICE.%ACTION"), "I'm foo.bar")

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

    def test_has_too_many_errors_remote(self):
        """Test the method has_too_many_errors remote."""
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

    def test_has_too_many_errors_local(self):
        """Test the method has_too_many_errors local."""
        service = Service('test_service')
        act_test = Action(name='test', command='/bin/true')
        service.add_action(act_test)
        service.run('test')
        last_action = service.last_action()
        self.assertFalse(last_action.has_too_many_errors())

        service.reset()
        act_test.errors = 1
        act_test.command = '/bin/false'
        service.run('test')
        last_action = service.last_action()
        self.assertFalse(last_action.has_too_many_errors())

        service.reset()
        act_test.errors = 0
        service.run('test')
        last_action = service.last_action()
        self.assertTrue(last_action.has_too_many_errors())

    def test_has_timed_out(self):
        """Test has_timed_out_method."""
        action = Action(name='start', target=HOSTNAME,
                    command='sleep 3', timeout=2)
        service = Service('test_service')
        service.add_action(action)
        service.run('start')
        last_action = service.last_action()
        self.assertTrue(last_action.has_timed_out())

    def test_set_retry(self):
        """Test retry assignement"""
        action =  Action(name='start', target=HOSTNAME, command='sleep 3')
        self.assertRaises(AssertionError, action.set_retry, 5)
        action =  Action(name='start', target=HOSTNAME, command='sleep 3',
                    delay=3)
        action.retry = 5
        self.assertEqual(action.retry, 5)

    def test_schedule(self):
        """Test behaviour method schedule"""
        a1 = Action(name='start', target=HOSTNAME, command='/bin/true')
        a2 = Action(name='status', target=HOSTNAME,
                    command='/bin/true', delay=3)
        ser = Service('TEST')
        ser.add_actions(a1, a2)
        a1.run()
        a2.run()
        self.assertTrue(0 < a1.duration and a1.duration < 0.5)
        self.assertTrue(2.8 < a2.duration and a2.duration < 3.5)

    def test_prepare_dep_success(self):
        """Test prepare an action with a single successful dependency"""
        a1 = Action('start', HOSTNAME, '/bin/true')
        a2 = Action('status', HOSTNAME, '/bin/true')
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
        a1 = Action('start', HOSTNAME, '/bin/true')
        a2 = Action('status', HOSTNAME, '/bin/false')
        ser = Service('TEST')
        a1.add_dep(a2)
        ser.add_actions(a1, a2)
        a1.run()
        self.assertEqual(a1.status, DONE)
        self.assertTrue(a1.duration)
        self.assertEqual(a2.status, ERROR)
        self.assertTrue(a2.duration)

    def test_prepare_actions_graph(self):
        """Test prepare an action graph without errors"""
        a1 = Action('start', HOSTNAME, '/bin/true')
        a2 = Action('start_engine', HOSTNAME, '/bin/true')
        a3 = Action('start_gui', HOSTNAME, '/bin/true')
        a4 = Action('empty_home', HOSTNAME, '/bin/true')
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
        a1 = Action('start', HOSTNAME, '/bin/true')
        a2 = Action('start_engine', HOSTNAME, '/bin/true')
        a3 = Action('start_gui', HOSTNAME, '/bin/false')
        a4 = Action('empty_home', HOSTNAME, '/bin/false')
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
        self.assertEqual(a3.status, ERROR)
        self.assertTrue(a3.duration)
        self.assertEqual(a4.status, ERROR)
        self.assertTrue(a4.duration)

    def test_action_with_variables(self):
        action = Action('start', HOSTNAME, 'echo \$([ "%VAR1" != "" ] && echo "-x %VAR1")')
        service = Service('TEST')
        service.add_actions(action)
        service.add_var('VAR1', 'foo')
        action.run()
