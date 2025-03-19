#
# Copyright CEA (2011-2017)
#

"""
This modules defines the tests cases targeting the BaseService
"""

import socket
import tempfile
from unittest import TestCase

from ClusterShell.NodeSet import NodeSet
from ClusterShell.Task import task_self

from MilkCheck.Engine.BaseEntity import NO_STATUS, DONE, ERROR, TIMEOUT, \
                                        DEP_ERROR, SKIPPED, WARNING
from MilkCheck.Engine.Action import Action, ActionManager, action_manager_self
from MilkCheck.Engine.Service import Service
from MilkCheckTests import setup_sshconfig, cleanup_sshconfig

HOSTNAME = socket.gethostname().split('.')[0]


class ActionTest(TestCase):
    """Define the unit tests for the object action."""

    def setUp(self):
        self.ssh_cfg = setup_sshconfig()

    def tearDown(self):
        cleanup_sshconfig(self.ssh_cfg)

    def test_desc(self):
        """Test action inherits 'desc'"""
        # No service description, no action description
        action1 = Action('status', command='/bin/true')
        service = Service('TEST')
        service.add_actions(action1)
        self.assertEqual(action1.desc, None)

        # Service description, actions inherits the description
        action2 = Action('status', command='/bin/true')
        service2 = Service('TEST2')
        service2.desc = "Service TEST"
        service2.add_actions(action2)
        action2.inherits_from(service2)
        self.assertEqual(action2.desc, "Service TEST")

    def test_skipped_action_overload(self):
        """Test action is not skipped if they overload target."""
        # A dep on ERROR
        dep = Service('dep')
        dep.add_action(Action('start', command='/bin/false'))
        # A service running on empty nodeset...
        svc = Service('foo', target='')
        # ... with an action overloading the empty nodeset
        svc.add_action(Action('start', target=HOSTNAME, command=':'))

        svc.add_dep(dep)
        svc.run('start')

        self.assertEqual(dep.status, ERROR)
        self.assertEqual(svc.status, DEP_ERROR)

    def test_action_instanciation(self):
        """Test instanciation of an action."""
        action = Action('start')
        self.assertNotEqual(action, None)
        self.assertEqual(action.name, 'start')

        action = Action(name='start', target=HOSTNAME, command='/bin/true')
        self.assertEqual(action.target, NodeSet(HOSTNAME))
        self.assertEqual(action.command, '/bin/true')

        action = Action(name='start', command='/bin/true', timeout=10, delay=5)
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
        action.maxretry = 5
        action.tries = 4
        action.worker = 'test'
        action.start_time = 1444253681.36017
        action.stop_time = 1444253681.36017
        action.reset()
        self.assertEqual(action.tries, 0)
        self.assertEqual(action.worker, None)
        self.assertEqual(action.start_time, None)
        self.assertEqual(action.stop_time, None)
        self.assertEqual(action.status, NO_STATUS)

    def test_nb_errors_remote(self):
        """Test the method nb_errors() (remote)."""
        action = Action(name='start', target='badname[12,13,21]',
                        command='/bin/false')
        action.errors = 2
        service = Service('test_service')
        service.add_action(action)
        service.run('start')
        self.assertEqual(action.nodes_error(), NodeSet("badname[12,13,21]"))
        self.assertEqual(action.nb_errors(), 3)
        self.assertEqual(action.status, ERROR)

    def test_nb_errors_remote2(self):
        """Test the method nb_errors() with no error (remote)."""
        action = Action(name='test', target=HOSTNAME, command='/bin/true')
        service = Service('test_service')
        service.add_action(action)
        service.run('test')
        self.assertEqual(action.nodes_error(), NodeSet())
        self.assertEqual(action.nb_errors(), 0)
        self.assertEqual(action.status, DONE)

    def test_nb_errors_local(self):
        """Test the method nb_errors() (local)"""
        service = Service('test_service')
        act_test = Action(name='test', command='/bin/true')
        service.add_action(act_test)
        service.run('test')
        self.assertEqual(act_test.nodes_error(), NodeSet())
        self.assertEqual(act_test.nb_errors(), 0)
        self.assertEqual(act_test.status, DONE)

        service.reset()
        act_test.errors = 1
        act_test.command = '/bin/false'
        service.run('test')
        self.assertEqual(act_test.nodes_error(), NodeSet("localhost"))
        self.assertEqual(act_test.nb_errors(), 1)
        self.assertEqual(act_test.status, WARNING)

        service.reset()
        act_test.errors = 1
        act_test.warnings = 1
        act_test.command = '/bin/false'
        service.run('test')
        self.assertEqual(act_test.nodes_error(), NodeSet("localhost"))
        self.assertEqual(act_test.nb_errors(), 1)
        self.assertEqual(act_test.status, DONE)

        service.reset()
        act_test.errors = 0
        service.run('test')
        self.assertEqual(act_test.nodes_error(), NodeSet("localhost"))
        self.assertEqual(act_test.nb_errors(), 1)
        self.assertEqual(act_test.status, ERROR)

        service.reset()
        act_test.errors = 0
        act_test.warnings = 1
        service.run('test')
        self.assertEqual(act_test.nodes_error(), NodeSet("localhost"))
        self.assertEqual(act_test.nb_errors(), 1)
        self.assertEqual(act_test.status, ERROR)

    def test_nb_timeout_remote(self):
        """Test nb_timeout() method (remote mode)"""
        action = Action(name='start', target=HOSTNAME,
                        command='sleep 3', timeout=0.5)
        service = Service('test_service')
        service.add_action(action)
        service.run('start')
        self.assertEqual(action.nodes_timeout(), NodeSet(HOSTNAME))
        self.assertEqual(action.nb_timeout(), 1)
        self.assertEqual(action.status, TIMEOUT)

    def test_nb_timeout_local(self):
        """Test nb_timeout() method (local)"""
        action = Action(name='start', command='sleep 3', timeout=0.3)
        service = Service('test_service')
        service.add_action(action)
        service.run('start')
        self.assertEqual(action.nodes_error(), NodeSet())
        self.assertEqual(action.nb_errors(), 0)
        self.assertEqual(action.nodes_timeout(), NodeSet("localhost"))
        self.assertEqual(action.nb_timeout(), 1)
        self.assertEqual(action.status, TIMEOUT)

    def test_mix_errors_timeout(self):
        """Test the result of mixed timeout and error actions."""
        # timeout host configuration is in setup_sshconfig (__init__.py)
        action = Action(name='start', target='badname,timeout,localhost',
                        command='/bin/true', timeout=0.9)
        action.errors = 1
        service = Service('test_service')
        service.add_action(action)
        service.run('start')
        self.assertEqual(action.nodes_error(), NodeSet('badname'))
        self.assertEqual(action.nb_errors(), 1)
        self.assertEqual(action.nodes_timeout(), NodeSet('timeout'))
        self.assertEqual(action.nb_timeout(), 1)
        self.assertEqual(action.status, ERROR)

        service.reset()
        action.errors = 2
        service.run('start')
        self.assertEqual(action.nodes_error(), NodeSet('badname'))
        self.assertEqual(action.nb_errors(), 1)
        self.assertEqual(action.nodes_timeout(), NodeSet('timeout'))
        self.assertEqual(action.nb_timeout(), 1)
        self.assertEqual(action.status, WARNING)

        service.reset()
        action.errors = 2
        action.warnings = 2
        service.run('start')
        self.assertEqual(action.nodes_error(), NodeSet('badname'))
        self.assertEqual(action.nb_errors(), 1)
        self.assertEqual(action.nodes_timeout(), NodeSet('timeout'))
        self.assertEqual(action.nb_timeout(), 1)
        self.assertEqual(action.status, DONE)

    def test_retry_error(self):
        """Test retry behaviour when errors"""
        action = Action('start', command='/bin/false')
        action.delay = 0.1
        action.maxretry = 3
        service = Service('retry')
        service.add_action(action)
        service.run('start')
        self.assertEqual(action.tries, 4)
        self.assertEqual(action.status, ERROR)
        self.assertTrue(0.3 < action.duration < 0.5,
                        "%.3f is not between 0.3 and 0.5" % action.duration)

    def test_retry_timeout(self):
        """Test retry behaviour when timeout"""
        action = Action('start', command='/bin/sleep 0.5', timeout=0.1)
        action.delay = 0.1
        action.maxretry = 2
        service = Service('retry')
        service.add_action(action)
        service.run('start')
        self.assertEqual(action.tries, 3)
        self.assertEqual(action.status, TIMEOUT)
        self.assertTrue(0.59 <= action.duration <= 0.8,
                        "%.3f is not between 0.59 and 0.8" % action.duration)

    def test_schedule(self):
        """Test behaviour method schedule"""
        a1 = Action(name='start', command='/bin/true')
        a2 = Action(name='status', command='/bin/true', delay=1)
        ser = Service('TEST')
        ser.add_actions(a1, a2)
        a1.run()
        a2.run()
        self.assertTrue(0 < a1.duration and a1.duration <= 0.2,
                        "%.3f is not between 0 and 0.2" % a1.duration)
        self.assertTrue(0.9 <= a2.duration and a2.duration <= 1.2,
                        "%.3f is not between 0.9 and 1.2" % a2.duration)

    def test_prepare_dep_success(self):
        """Test prepare an action with a single successful dependency"""
        a1 = Action('start', command='/bin/true')
        a2 = Action('status', command='/bin/true')
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
        a1 = Action('start', command='/bin/true')
        a2 = Action('status', command='/bin/false')
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
        a1 = Action('start', command='/bin/true')
        a2 = Action('start_engine', command='/bin/true')
        a3 = Action('start_gui', command='/bin/true')
        a4 = Action('empty_home', command='/bin/true')
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
        a1 = Action('start', command='/bin/true')
        a2 = Action('start_engine', command='/bin/true')
        a3 = Action('start_gui', command='/bin/false')
        a4 = Action('empty_home', command='/bin/false')
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
        """Test variables in action command"""
        cmd = 'echo %([ "%VAR1" != "" ] && echo "-x %VAR1")'
        action = Action('start', command=cmd)
        service = Service('TEST')
        service.add_actions(action)
        service.add_var('VAR1', 'foo')
        service.resolve_all()
        action.run()
        self.assertEqual(action.worker.command, 'echo -x foo')

    def test_failed_nodes(self):
        """failed nodes are backup"""
        action = Action('start', command='/bin/false', target=HOSTNAME)
        service = Service('test')
        service.add_actions(action)
        action.run()
        self.assertEqual(action.failed_nodes, NodeSet(HOSTNAME))
        self.assertEqual(action.status, ERROR)
        # This is propagated to action service
        self.assertEqual(service.failed_nodes, action.failed_nodes)


class ActionFromDictTest(TestCase):
    '''Test cases for Action.fromdict()'''

    def test_create_action1(self):
        '''Test instanciation of an Action through a dictionnary'''
        act = Action('start')
        act.fromdict(
            {
                'target': 'localhost',
                'fanout': 4,
                'retry': 5,
                'delay': 2,
                'errors': 3,
                'timeout': 4,
                'cmd': '/bin/True',
                'desc': 'my desc',
                'mode': 'delegate',
            }
        )
        self.assertTrue(act)
        self.assertEqual(act.name, 'start')
        self.assertEqual(act.target, NodeSet('localhost'))
        self.assertEqual(act.fanout, 4)
        self.assertEqual(act.maxretry, 5)
        self.assertEqual(act.errors, 3)
        self.assertEqual(act.delay, 2)
        self.assertEqual(act.timeout, 4)
        self.assertEqual(act.command, '/bin/True')
        self.assertEqual(act.desc, 'my desc')
        self.assertEqual(act.mode, 'delegate')

    def test_create_action2(self):
        '''Test instanciation of an action with variables'''
        act = Action('start')
        act.fromdict(
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
        )
        self.assertTrue(act)
        self.assertTrue(len(act.variables) == 2)
        self.assertTrue('var1' in act.variables)
        self.assertTrue('var2' in act.variables)

    def test_resolve_all(self):
        """resolve_all() resolves in all Action properties"""
        act = Action('start')
        act.fromdict({
                        'variables': {
                            'label': 'Start action',
                         },
                        'desc': "%label",
                        'cmd': 'service foo %ACTION'
                     })
        act.resolve_all()
        self.assertEqual(act.desc, "Start action")
        self.assertEqual(act.command, "service foo start")

    def test_action_skip(self):
        """Test skip method for actions"""
        action = Action(name='start', target=HOSTNAME, command='/bin/true')
        action.skip()
        self.assertTrue(action.to_skip())


class ActionManagerTest(TestCase):
    """Test cases for action_manager_self"""

    def setUp(self):
        ActionManager._instance = None

    def tearDown(self):
        ActionManager._instance = None
        task_self().topology = None

    def assert_near(self, target, delta, value):
        """Like self.assertTrue(target - delta < value < target + delta)"""
        low = target - delta
        high = target + delta
        self.assertTrue(low <= value <= high,
                        "%.2f is not [%f and %f]" % (value, low, high))

    def test_instanciation(self):
        """Test singleton handling of action_manager_self"""
        task_manager = action_manager_self()
        other_task_manager = action_manager_self()
        self.assertTrue(task_manager is other_task_manager)

    def test_add_task(self):
        """Test the behaviour of the add_task method"""
        task_manager = action_manager_self()
        task1 = Action('start')
        task1.fanout = 60
        task2 = Action('stop')
        task2.fanout = 12
        task3 = Action('status')
        task3.fanout = 50
        task_manager.add_task(task1)
        task_manager.add_task(task2)
        task_manager.add_task(task3)
        task_manager.add_task(task3)
        self.assertEqual(task_manager.fanout, 12)
        task4 = Action('check')
        task4.fanout = 3
        task_manager.add_task(task4)
        self.assertEqual(task_manager.fanout, 3)
        self.assertEqual(task_manager.tasks_count, 4)
        self.assertEqual(task_manager.tasks_done_count, 4)

    def test_add_task_weird_values(self):
        """Test the method add task with task without fanout"""
        task_manager = action_manager_self()
        task1 = Action('start')
        task1.fanout = 60
        task2 = Action('stop')
        task3 = Action('status')
        task3.fanout = 50
        task_manager.add_task(task1)
        task_manager.add_task(task2)
        task_manager.add_task(task3)
        self.assertEqual(task_manager.fanout, 50)
        self.assertEqual(task_manager.tasks_count, 3)

    def test_remove_task(self):
        """Test the behaviour of the remove_task method"""
        task_manager = action_manager_self()
        task1 = Action('start')
        task1.fanout = 260
        task2 = Action('stop')
        task2.fanout = 85
        task3 = Action('status')
        task3.fanout = 85
        task4 = Action('check')
        task4.fanout = 148
        task_manager.add_task(task1)
        task_manager.add_task(task2)
        task_manager.add_task(task3)
        task_manager.add_task(task4)
        self.assertEqual(task_manager.fanout, 85)
        task_manager.remove_task(task2)
        self.assertEqual(task_manager.fanout, 85)
        task_manager.remove_task(task3)
        self.assertEqual(task_manager.fanout, 148)
        task_manager.remove_task(task4)
        self.assertEqual(task_manager.fanout, 260)
        task_manager.remove_task(task1)
        self.assertFalse(task_manager.fanout)
        self.assertEqual(task_manager.tasks_count, 0)
        self.assertEqual(task_manager.tasks_done_count, 4)

    def test__is_running_task(self):
        """Test the behaviour of the method _is_running_task"""
        task_manager = action_manager_self()
        task1 = Action('start')
        task1.fanout = 260
        task2 = Action('stop')
        task2.fanout = 85
        task3 = Action('status')
        task3.fanout = 148
        task4 = Action('check')
        task_manager.add_task(task1)
        task_manager.add_task(task3)
        task_manager.add_task(task4)
        self.assertTrue(task_manager._is_running_task(task3))
        self.assertTrue(task_manager._is_running_task(task4))
        self.assertRaises(AssertionError, task_manager._is_running_task, None)
        self.assertFalse(task_manager._is_running_task(task2))

    def test_set_of_running_task(self):
        """
        Test return a sets of running tasks from the property running_tasks
        """
        task_manager = action_manager_self()
        task1 = Action('start')
        task1.fanout = 260
        task2 = Action('stop')
        task2.fanout = 85
        task3 = Action('status')
        task3.fanout = 148
        task_manager.add_task(task1)
        task_manager.add_task(task2)
        task_manager.add_task(task3)
        self.assertTrue(task_manager.running_tasks)
        self.assertEqual(len(task_manager.running_tasks), 3)

    def test_perform_action(self):
        """test perform an action without any delay"""
        action = Action('start', command='/bin/true')
        ser = Service('TEST')
        ser.add_action(action)
        ser.run('start')
        task_manager = action_manager_self()
        self.assertEqual(task_manager.tasks_done_count, 1)
        self.assertTrue(action.duration < 0.5,
                        "Too long: %.2f > 0.5" % action.duration)

    def test_perform_action_bad_service(self):
        '''test perform action with a simulate service hooked to the action'''
        action = Action(name='start', command=':')
        ser = Service('TEST')
        ser.simulate = True
        ser.add_action(action)
        ser.run('start')
        task_manager = action_manager_self()
        self.assertEqual(task_manager.tasks_done_count, 0)

    def test_perform_delayed_action_bad_service(self):
        '''
        test perform delayed action with a simulate service hooked to
        the action
        '''
        action = Action(name='start', command=':', timeout=0.01)
        ser = Service('TEST')
        ser.simulate = True
        ser.add_action(action)
        ser.run('start')
        task_manager = action_manager_self()
        self.assertEqual(task_manager.tasks_done_count, 0)

    def test_perform_delayed_action(self):
        """test perform an action with a delay"""
        action = Action('start', command='sleep 0.3')
        ser = Service('TEST')
        ser.add_action(action)
        ser.run('start')
        task_manager = action_manager_self()
        ActionManager._instance = None
        self.assertEqual(task_manager.tasks_done_count, 1)
        self.assert_near(0.3, 0.1, action.duration)

    def test_perform_remote_false_action(self):
        """Test perform an action in remote mode=False"""

        action = Action('start', command='hostname -s', target='node1')
        action.remote = False
        svc = Service('Local')
        svc.add_action(action)

        mytopo = tempfile.NamedTemporaryFile('w')
        mytopo.write(u"[routes]\n%s: node1\n" % HOSTNAME)
        mytopo.flush()
        task_self().load_topology(mytopo.name)
        mytopo.close()

        svc.run('start')
        buff = action.worker.node_buffer('node1').decode()
        self.assertEqual(buff, HOSTNAME)

    def test_exec_mode(self):
        """Test exec mode"""
        action = Action(name='start', command='echo %%h %%rank',
                        target='%s,localhost' % HOSTNAME)
        action.mode = 'exec'
        svc = Service('test')
        svc.add_action(action)
        svc.resolve_all()
        svc.run('start')

        # Need 2 checks because we do not know which target will be used first
        outputs = [action.worker.node_buffer(HOSTNAME).decode(),
                   action.worker.node_buffer('localhost').decode()]
        self.assertTrue(outputs == ["%s 0" % HOSTNAME, "localhost 1"] or
                        outputs == ["%s 1" % HOSTNAME, "localhost 0"])
