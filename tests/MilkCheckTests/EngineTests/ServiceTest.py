# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This modules defines the tests cases targeting the Action and Service objects.
"""
from unittest import TestCase
import socket

# Classes
from MilkCheck.Engine.Service import Service
from MilkCheck.Engine.Action import Action
from ClusterShell.NodeSet import NodeSet

# Exceptions
from MilkCheck.Engine.Service import ActionAlreadyReferencedError
from MilkCheck.Engine.Service import ActionNotFoundError

# Symbols
from MilkCheck.Engine.BaseEntity import NO_STATUS, DONE, TIMEOUT, DEP_ERROR
from MilkCheck.Engine.BaseEntity import ERROR, WAITING_STATUS, SKIPPED
from MilkCheck.Engine.BaseEntity import WARNING, LOCKED, MISSING, CHECK, REQUIRE_WEAK
        
HOSTNAME = socket.gethostname().split('.')[0]

class ServiceTest(TestCase):
    """Define the unit tests for the object service."""

    def assertNear(self, target, delta, value):
        if value > target + delta:
            self.assertEqual(target, value)
        if value < target - delta:
            self.assertEqual(target, value)

    def test_service_instanciation(self):
        """Test instanciation of a service."""
        service = Service('brutus')
        self.assertNotEqual(service, None, 'should be none')
        self.assertEqual(service.name, 'brutus', 'wrong name')

    def test_inheritance(self):
        '''Test inheritance between action and services'''
        ser1 = Service('parent')
        ser1.target = '127.0.0.1'
        ser2 = Service('inherited')
        ser2.add_action(Action('start'))
        ser2.add_action(Action('stop', HOSTNAME))
        ser2.inherits_from(ser1)
        self.assertEqual(ser2.target, NodeSet('127.0.0.1'))
        self.assertEqual(ser2._actions['start'].target, NodeSet('127.0.0.1'))
        self.assertEqual(ser2._actions['stop'].target, NodeSet(HOSTNAME))

    def test_local_variables(self):
        '''Test Service local variables'''
        self.assertEqual(Service('foo')._resolve("I'm %SERVICE"), "I'm foo")

    def test_update_target(self):
        '''Test update of the target of an service'''
        serv = Service('A')
        act = Action('start', 'fortoy[5-10]', '/bin/true')
        serv.add_action(act)
        serv.update_target('aury[1-12]^fortoy[3-6]')
        self.assertTrue(serv.target == NodeSet('aury[1-12]^fortoy[3-6]'))
        self.assertTrue(act.target == NodeSet('aury[1-12]^fortoy[3-6]'))

    def test_reset_service(self):
        '''Test resest values of a service'''
        service = Service('brutus')
        action = Action('start')
        action.status = DONE 
        service.add_action(action)
        service._last_action = 'start'
        service.reset()
        self.assertFalse(service._last_action)
        self.assertEqual(action.status, NO_STATUS)
        self.assertEqual(service.status, NO_STATUS)

    def test_add_action(self):
        """Test add_action's behaviour."""
        service = Service('brutus')
        service.add_action(Action('start'))
        self.assertTrue(service.has_action('start'))
        self.assertRaises(ActionAlreadyReferencedError,
                service.add_action,Action('start'))
        self.assertRaises(TypeError,
                service.add_action,None)

    def test_add_actions(self):
        """Test the possibility to add multiple actions at the same time"""
        service = Service('SERV')
        act_a = Action('start', HOSTNAME, '/bin/true')
        act_b = Action('stop', HOSTNAME, '/bin/true')
        act_c = Action('status', HOSTNAME, '/bin/true')
        service.add_actions(act_a, act_b, act_c)
        self.assertTrue(service.has_action('start'))
        self.assertTrue(service.has_action('stop'))
        self.assertTrue(service.has_action('status'))

    def test_remove_action(self):
        """Test remove_action behaviour."""
        service = Service('brutus')
        service.add_action(Action('start'))
        service.remove_action('start')
        self.assertFalse(service.has_action('start'))
        self.assertRaises(ActionNotFoundError,
            service.remove_action, 'start')

    def test_last_action(self):
        """Test last_action method behaviour."""
        service = Service('Test')
        self.assertRaises(ActionNotFoundError, service.last_action)

        start = Action('start', HOSTNAME, '/bin/true')
        service.add_action(start)
        self.assertRaises(ActionNotFoundError, service.last_action)
        service.prepare('start')
        self.assertTrue(service.last_action())
        self.assertTrue(service.last_action() is start)

    def test_prepare_single_service(self):
        """Test prepare without dependencies between services."""
        serv_test = Service('test_service')
        ac_start = Action(name='start', target=HOSTNAME, command='/bin/true')
        serv_test.add_action(ac_start)
        serv_test.run('start')
        self.assertEqual(serv_test.status, DONE)

    def test_prepare_one_dependency(self):
        """Test prepare with one dependency."""
        # Define the main service
        serv_test = Service('test_service')
        start = Action(name='start', target=HOSTNAME, command='/bin/true')
        start2 = Action(name='start', target=HOSTNAME, command='/bin/true')
        serv_test.add_action(start)

        # Define the single dependency of the main service
        serv_dep = Service('dependency')
        serv_dep.add_action(start2)
        serv_test.add_dep(serv_dep)

        # Start preparing of the base service
        serv_test.run('start')
        self.assertEqual(serv_test.status, DONE)
        self.assertEqual(serv_dep.status, DONE)

    def test_prepare_several_dependencies(self):
        """Test prepare with several dependencies at the same level."""
        # Define the main service
        serv_test = Service('test_service')
        start = Action(name='start', target=HOSTNAME, command='/bin/true')
        start2 = Action(name='start', target=HOSTNAME, command='/bin/true')
        start3 = Action(name='start', target=HOSTNAME, command='/bin/true')
        serv_test.add_action(start)

        # Define the dependency DEP_A
        serv_depa = Service('DEP_A')
        serv_depa.add_action(start2)

        # Define the dependency DEP_B
        serv_depb = Service('DEP_B')
        serv_depb.add_action(start3)

        serv_test.add_dep(serv_depa)
        serv_test.add_dep(serv_depb)

        serv_test.run('start')
        self.assertEqual(serv_test.status, DONE)
        self.assertEqual(serv_depa.status, DONE)
        self.assertEqual(serv_depb.status, DONE)

    def test_run_with_skipped_deps(self):
        """Test run with only SKIPPED dependencies"""

        # Define the main service
        serv_test = Service('test_service')
        start = Action(name='start', target=HOSTNAME, command='/bin/true')
        serv_test.add_action(start)

        serv_depa = Service('DEP_A')
        serv_depa.status = SKIPPED
        serv_depb = Service('DEP_B')
        serv_depb.status = SKIPPED

        serv_test.add_dep(serv_depa)
        serv_test.add_dep(serv_depb)

        self.assertEqual(serv_test.eval_deps_status(), SKIPPED)

        serv_test.run('start')
        self.assertEqual(serv_test.status, DONE)
        self.assertEqual(serv_depa.status, SKIPPED)
        self.assertEqual(serv_depb.status, SKIPPED)

    def test_prepare_multilevel_dependencies(self):
        """Test prepare with multiple dependencies at different levels."""
        #Service Arthemis is delcared here
        arth = Service('arthemis')
        arth.desc = 'Sleep five seconds'
        start = Action(name='start', target=HOSTNAME, command='/bin/true')
        start2 = Action(name='start', target=HOSTNAME, command='/bin/true')
        start3 = Action(name='start', target=HOSTNAME, command='/bin/true')
        start4 = Action(name='start', target=HOSTNAME, command='/bin/true')
        arth.add_action(start)

        # Service Chiva is declared here
        chiva = Service('chiva')
        chiva.desc = 'List all processes in details'
        chiva.add_action(start2)
        chiva.add_dep(arth)

        # Service Dyonisos is declared here
        dion = Service('dionysos')
        dion.desc = 'Perform tree on directory specified'
        dion.add_action(start3)
        dion.add_dep(arth)

        # Service Brutus is declared here
        brut = Service('brutus')
        brut.desc = 'Wanna sleep all the time'
        brut.add_action(start4)

        brut.add_dep(chiva)
        brut.add_dep(dion)

        brut.run('start')
        self.assertEqual(arth.status, DONE)
        self.assertEqual(chiva.status, DONE)
        self.assertEqual(dion.status, DONE)
        self.assertEqual(brut.status, DONE)

    def test_prepare_require_weak(self):
        """Test weak require dependency error."""
        serv = Service('BASE')
        serv_a = Service('DEP_A')
        serv_b = Service('DEP_B')

        suc = Action(name='start', target=HOSTNAME, command='/bin/true')
        suc2 = Action(name='start', target=HOSTNAME, command='/bin/true')
        ac_err = Action(name='start', target=HOSTNAME, command='/bin/false')

        serv.add_action(suc)
        serv_a.add_action(ac_err)
        serv_b.add_action(suc2)

        serv.add_dep(serv_b)
        serv.add_dep(serv_a, REQUIRE_WEAK)

        serv.run('start')

        self.assertEqual(serv.status, WARNING)
        self.assertEqual(serv_a.status, ERROR)
        self.assertEqual(serv_b.status, DONE)

    def test_prepare_require_strong(self):
        """Test strong require dependency error."""
        serv = Service('BASE')
        serv_a = Service('DEP_A')
        serv_b = Service('DEP_B')

        ac_suc = Action(name='start', target=HOSTNAME, command='/bin/true')
        ac_suc2 = Action(name='start', target=HOSTNAME, command='/bin/true')
        ac_err = Action(name='start', target=HOSTNAME, command='/bin/false')

        serv.add_action(ac_suc)
        serv_a.add_action(ac_err)
        serv_b.add_action(ac_suc2)

        serv.add_dep(serv_b)
        serv.add_dep(serv_a)

        serv.run('start')

        self.assertEqual(serv.status, DEP_ERROR)
        self.assertEqual(serv_a.status, ERROR)
        self.assertEqual(serv_b.status, DONE)

    def test_prepare_errors_same_level(self):
        """Test prepare behaviour with two errors at the same level"""
        serv = Service('BASE')
        serv_a = Service('DEP_A')
        serv_b = Service('DEP_B')
        serv_c = Service('DEP_C')

        ac_suc = Action(name='start', target=HOSTNAME, command='/bin/true')
        ac_suc2 = Action(name='start', target=HOSTNAME, command='/bin/true')
        ac_err = Action(name='start', target=HOSTNAME, command='/bin/false')
        ac_err2 = Action(name='start', target=HOSTNAME, command='dlvlfvlf')

        serv.add_action(ac_suc)
        serv_a.add_action(ac_suc2)
        serv_b.add_action(ac_err)
        serv_c.add_action(ac_err2)

        serv.add_dep(serv_a)
        serv_a.add_dep(serv_b)
        serv_a.add_dep(serv_c)

        serv.run('start')

        self.assertEqual(serv.status, DEP_ERROR)
        self.assertEqual(serv_a.status, DEP_ERROR)
        self.assertEqual(serv_b.status, ERROR)
        self.assertEqual(serv_c.status, ERROR)
        
    def test_prepare_with_multiple_require_errors(self):
        """Test multiple require dependencies errors at different levels."""
        serv_base_error = Service('A')
        serv_ok_warnings = Service('B')
        serv_error = Service('C')
        serv_timeout = Service('D')

        ac_suc = Action(name='start', target=HOSTNAME, command='/bin/true')
        ac_suc2 = Action(name='start', target=HOSTNAME, command='/bin/true')
        ac_suc3 = Action(name='start', target=HOSTNAME, command='/bin/true')
        ac_tim = Action(name='start', target=HOSTNAME,
                        command='sleep 3', timeout=0.5)

        serv_base_error.add_action(ac_suc)
        serv_ok_warnings.add_action(ac_suc2)
        serv_error.add_action(ac_suc3)
        serv_timeout.add_action(ac_tim)

        serv_base_error.add_dep(serv_ok_warnings)
        serv_base_error.add_dep(serv_error)
        serv_ok_warnings.add_dep(serv_timeout, REQUIRE_WEAK)
        serv_error.add_dep(serv_timeout)

        serv_base_error.run('start')

        self.assertEqual(serv_base_error.status, DEP_ERROR)
        self.assertEqual(serv_ok_warnings.status, WARNING)
        self.assertEqual(serv_error.status, DEP_ERROR)
        self.assertEqual(serv_timeout.status, TIMEOUT)

    def test_prepare_multiple_errors(self):
        """Test prepare with check and require deps with errors."""
        serv_a = Service('BASE')
        serv_b = Service('DEP_B')
        serv_c = Service('DEP_C')
        serv_d = Service('DEP_D')
        serv_x = Service('DEP_VX')
        serv_k = Service('DEP_K')

        act_suc = Action(name='start', target=HOSTNAME, command='/bin/true')
        act_suc2 = Action(name='start', target=HOSTNAME, command='/bin/true')
        act_suc3 = Action(name='start', target=HOSTNAME, command='/bin/true')
        act_suc4 = Action(name='start', target=HOSTNAME, command='/bin/true')
        act_suc5 = Action(name='start', target=HOSTNAME, command='/bin/true')
        act_status_failed = Action(name='status', target=HOSTNAME,
            command='/bin/false')
        act_status = Action(name='status', target=HOSTNAME,
                            command='/bin/true')

        serv_a.add_action(act_suc)
        serv_b.add_action(act_suc2)
        serv_c.add_action(act_suc3)
        serv_d.add_action(act_suc4)
        serv_d.add_action(act_status)
        serv_x.add_action(act_suc5)
        serv_k.add_action(act_status_failed)

        serv_a.add_dep(serv_x)
        serv_a.add_dep(serv_b)
        serv_a.add_dep(serv_c, REQUIRE_WEAK)

        serv_b.add_dep(serv_d, CHECK)

        serv_c.add_dep(serv_d)
        serv_c.add_dep(serv_k, CHECK)

        serv_a.run('start')

        self.assertEqual(serv_d.status, DONE)
        self.assertEqual(serv_k.status, ERROR)
        self.assertEqual(serv_c.status, DEP_ERROR)
        self.assertEqual(serv_b.status, DONE)
        self.assertEqual(serv_x.status, DONE)
        self.assertEqual(serv_a.status, WARNING)
        
    def test_prepare_delayed_action(self):
        """Test prepare Service with a delayed action"""
        serv = Service('DELAYED_SERVICE')
        act_suc = ac_suc = Action(name='start',
                    target=HOSTNAME, command='/bin/true', delay=1)
        serv.add_action(act_suc)
        serv.run('start')
        self.assertEqual(serv.status, DONE)
        action_done = serv.last_action()
        self.assertNear(1.0, 0.3, action_done.duration)

    def test_prepare_multiple_delay(self):
        '''Test prepare with dependencies and multiple delay'''
        serv = Service('BASE_DELAYED')
        serv_a = Service('A_NOT_DELAYED')
        serv_b = Service('B_DELAYED')
        serv_c = Service('C_DELAYED')
        act_a = Action(name='start',
                    target=HOSTNAME, command='/bin/true')
        act_serv = Action(name='start',
                    target=HOSTNAME, command='/bin/true', delay=0.5)
        act_b = Action(name='start',
                    target=HOSTNAME, command='/bin/true', delay=0.5)
        act_c = Action(name='start',
                    target=HOSTNAME, command='/bin/true', delay=1)
        serv.add_action(act_serv)
        serv_a.add_action(act_a)
        serv_b.add_action(act_b)
        serv_c.add_action(act_c)
        serv.add_dep(serv_a)
        serv.add_dep(serv_b)
        serv_a.add_dep(serv_c)
        serv_b.add_dep(serv_c)
        serv.run('start')
        self.assertEqual(serv.status, DONE)
        action = serv.last_action()
        self.assertNear(0.5, 0.3, action.duration)
        self.assertEqual(serv_a.status, DONE)
        action = serv_a.last_action()
        self.assertNear(0.0, 0.3, action.duration)
        self.assertEqual(serv_b.status, DONE)
        action = serv_b.last_action()
        self.assertNear(0.5, 0.3, action.duration)
        self.assertEqual(serv_c.status, DONE)
        action = serv_c.last_action()
        self.assertNear(1.0, 0.3, action.duration)

    def test_run_partial_deps(self):
        """Test stop algorithm as soon as the calling point is done."""
        serv = Service('NOT_CALLED')
        serv_a = Service('CALLING_POINT')
        serv_b = Service('SERV_1')
        serv_c = Service('SERV_2')
        act_suc = Action('start', HOSTNAME, '/bin/true')
        act_suc2 = Action('start', HOSTNAME, '/bin/true')
        act_suc3 = Action('start', HOSTNAME, '/bin/true')
        serv_a.add_action(act_suc)
        serv_b.add_action(act_suc2)
        serv_c.add_action(act_suc3)
        serv.add_dep(serv_a)
        serv_a.add_dep(serv_b)
        serv_a.add_dep(serv_c)
        serv_a.run('start')
        self.assertEqual(serv.status, NO_STATUS)
        self.assertEqual(serv_a.status, DONE)
        self.assertEqual(serv_b.status, DONE)
        self.assertEqual(serv_c.status, DONE)

    def test_run_action_with_subaction(self):
        """Test action running a successful sub action (start->status)"""
        serv = Service('BASE')
        act_start = Action('start', HOSTNAME, '/bin/true')
        act_status = Action('status', HOSTNAME, '/bin/true')
        act_start.add_dep(target=act_status)
        serv.add_actions(act_start, act_status)
        serv.run('start')
        self.assertEqual(serv.status, DONE)
        self.assertFalse(act_start.duration)
        self.assertTrue(act_status.duration)
        
    def test_run_action_with_failed_subaction(self):
        """Test action running a failed sub action (start->status)"""
        serv = Service('BASE')
        act_start = Action('start', HOSTNAME, '/bin/true')
        act_status_fail = Action('status', HOSTNAME, '/bin/false')
        act_start.add_dep(target=act_status_fail)
        serv.add_actions(act_start, act_status_fail)
        serv.run('start')
        self.assertEqual(serv.status, DONE)
        self.assertTrue(act_start.duration)
        self.assertTrue(act_status_fail.duration)

    def test_run_multiple_action_with_subaction(self):
        """Test with multiple actions running a sub action (start-> status)"""
        nemesis = Service("NEMESIS")
        zombie_one = Service("ZOMBIE_ONE")
        zombie_two = Service("ZOMBIE_TWO")
        hive = Service("THE_HIVE")

        act_start1 = Action("start", HOSTNAME, "/bin/true")
        act_start2 = Action("start", HOSTNAME, "/bin/false")
        act_start3 = Action("start", HOSTNAME, "/bin/true")
        act_start4 = Action("start", HOSTNAME, "/bin/true")
        act_sta = Action("status", HOSTNAME, "/bin/true")
        act_sta_fai = Action("status", HOSTNAME, "/bin/false")

        act_start2.add_dep(act_sta_fai)
        act_start4.add_dep(act_sta)

        nemesis.add_action(act_start1)
        zombie_one.add_actions(act_start2, act_sta_fai)
        zombie_two.add_action(act_start3)
        hive.add_actions(act_start4, act_sta)

        zombie_one.add_dep(hive)
        zombie_two.add_dep(hive)
        nemesis.add_dep(zombie_one)
        nemesis.add_dep(zombie_two)

        nemesis.run("start")
        self.assertEqual(hive.status, DONE)
        self.assertEqual(zombie_one.status, ERROR)
        self.assertEqual(zombie_two.status, DONE)
        self.assertEqual(nemesis.status, DEP_ERROR)
        self.assertFalse(act_start1.duration)
        self.assertTrue(act_start2.duration)
        self.assertTrue(act_start3.duration)
        self.assertFalse(act_start4.duration)
        self.assertTrue(act_sta_fai.duration)
        self.assertTrue(act_sta.duration)

    def test_run_reverse_single_service(self):
        """Test run action stop on service (reverse algorithm)"""
        ser = Service('REVERSE')
        ser.algo_reversed = True
        stop = Action('stop', HOSTNAME, '/bin/true')
        ser.add_action(stop)
        ser.run('stop')
        self.assertEqual(ser.status, DONE)
        self.assertTrue(stop.duration)

    def test_run_reverse_with_dependencies(self):
        ser = Service('REVERSE_BASE')
        ser_dep = Service('REVERSE_DEP')
        ser.algo_reversed = True
        ser_dep.algo_reversed = True
        stop1 = Action('stop', HOSTNAME, '/bin/true')
        stop2 = Action('stop', HOSTNAME, '/bin/true')
        ser.add_action(stop1)
        ser_dep.add_action(stop2)
        ser.add_dep(ser_dep)
        ser_dep.run('stop')
        self.assertEqual(ser.status, DONE)
        self.assertTrue(stop1.duration)
        self.assertEqual(ser_dep.status, DONE)
        self.assertTrue(stop2.duration)

    def test_run_revese_multiple_services(self):
        """Test run stop action on service provokes reverse algorithm"""
        """Test prepare with multiple dependencies at different levels."""
        #Service Arthemis is delcared here
        arth = Service('arthemis')
        arth.algo_reversed = True
        stop = Action(name='stop', target=HOSTNAME, command='/bin/true')
        stop2 = Action(name='stop', target=HOSTNAME, command='/bin/true')
        stop3 = Action(name='stop', target=HOSTNAME, command='/bin/true')
        stop4 = Action(name='stop', target=HOSTNAME, command='/bin/true')
        arth.add_action(stop)

        # Service Chiva is declared here
        chiva = Service('chiva')
        chiva.algo_reversed = True
        chiva.add_action(stop2)
        chiva.add_dep(arth)

        # Service Dyonisos is declared here
        dion = Service('dionysos')
        dion.algo_reversed = True
        dion.add_action(stop3)
        dion.add_dep(arth)

        # Service Brutus is declared here
        brut = Service('brutus')
        brut.algo_reversed = True
        brut.add_action(stop4)

        brut.add_dep(chiva)
        brut.add_dep(dion)

        arth.run('stop')
        self.assertEqual(arth.status, DONE)
        self.assertTrue(stop.duration)
        self.assertEqual(chiva.status, DONE)
        self.assertTrue(stop2.duration)
        self.assertEqual(dion.status, DONE)
        self.assertTrue(stop3.duration)
        self.assertEqual(brut.status, DONE)
        self.assertTrue(stop4.duration)

    def test_run_with_locked_service(self):
        '''Test run services with locked dependencies'''
        s1 = Service('S1')
        s2 = Service('S2')
        s3 = Service('S3')
        s4 = Service('S4')
        s5 = Service('S5')

        # Actions S1
        start_s1 = Action('start', HOSTNAME, '/bin/true')
        stop_s1 = Action('stop', HOSTNAME, '/bin/true')
        s1.add_actions(start_s1, stop_s1)
        # Actions S2
        start_s2 = Action('start', HOSTNAME, '/bin/true')
        stop_s2 = Action('stop', HOSTNAME, '/bin/true')
        s2.add_actions(start_s2, stop_s2)
        # Actions S3
        start_s3 = Action('start', HOSTNAME, '/bin/false')
        stop_s3 = Action('stop', HOSTNAME, '/bin/false')
        s3.add_actions(start_s3, stop_s3)
        # Actions S4
        start_s4 = Action('start', HOSTNAME, '/bin/true')
        stop_s4 = Action('stop', HOSTNAME, '/bin/true')
        s4.add_actions(start_s4, stop_s4)
        # Actions I1
        start_s5 = Action('start', HOSTNAME, '/bin/true')
        stop_s5 = Action('stop', HOSTNAME, '/bin/true')
        s5.add_actions(start_s5, stop_s5)

        # Locked services
        s3.status = LOCKED

        # Build graph
        s1.add_dep(target=s2)
        s1.add_dep(target=s3)
        s3.add_dep(target=s4)
        s3.add_dep(target=s5)
        
        # Run service S1
        s1.run('start')

        self.assertEqual(s1.status, DONE)
        self.assertEqual(s2.status, DONE)
        self.assertEqual(s3.status, LOCKED)
        self.assertEqual(s4.status, NO_STATUS)
        self.assertEqual(s5.status, NO_STATUS)

    def test_missing_action(self):
        """Test prepare with service with missing action is ok"""

        # Graph leaf has no 'status' action
        s1 = Service("1")
        s1.add_action(Action('start', HOSTNAME, '/bin/true'))
        s1.add_action(Action('status', HOSTNAME, '/bin/true'))
        s2 = Service("2")
        s2.add_action(Action('start', HOSTNAME, '/bin/true'))
        s2.add_dep(s1)
        s2.run('status')
        self.assertEqual(s1.status, DONE)
        self.assertEqual(s2.status, MISSING)

        s1.reset()
        s2.reset()
        self.assertEqual(s1.status, NO_STATUS)
        self.assertEqual(s2.status, NO_STATUS)

        # 'status' action is propagated to leaf even if '2' has not the
        # requested action.
        s3 = Service("3")
        s3.add_action(Action('start', HOSTNAME, '/bin/true'))
        s3.add_action(Action('status', HOSTNAME, '/bin/true'))
        s3.add_dep(s2)
        s3.run('status')
        self.assertEqual(s1.status, DONE)
        self.assertEqual(s2.status, MISSING)
        self.assertEqual(s3.status, DONE)
