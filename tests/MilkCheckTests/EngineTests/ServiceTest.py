#
# Copyright CEA (2011-2017)
#

"""
This modules defines the tests cases targeting the Action and Service objects.
"""
from unittest import TestCase

# Classes
from MilkCheck.Engine.Action import Action
from MilkCheck.Engine.Service import Service
from ClusterShell.NodeSet import NodeSet

# Exceptions
from MilkCheck.Engine.Service import ActionAlreadyReferencedError
from MilkCheck.Engine.Service import ActionNotFoundError

# Symbols
from MilkCheck.Engine.BaseEntity import NO_STATUS, DONE, TIMEOUT, DEP_ERROR
from MilkCheck.Engine.BaseEntity import ERROR, SKIPPED
from MilkCheck.Engine.BaseEntity import LOCKED, MISSING, CHECK, REQUIRE_WEAK, \
                                        FILTER, REQUIRE

from MilkCheckTests import setup_sshconfig, cleanup_sshconfig

import socket
HOSTNAME = socket.gethostname().split('.')[0]

class ServiceTest(TestCase):
    """Define the unit tests for the object service."""

    def setUp(self):
        self.ssh_cfg = setup_sshconfig()

    def tearDown(self):
        cleanup_sshconfig(self.ssh_cfg)

    def assert_near(self, target, delta, value):
        """Like self.assertTrue(target - delta < value < target + delta)"""
        low = target - delta
        high = target + delta
        self.assertTrue(low <= value <= high,
                        "%.2f is not [%f and %f]" % (value, low, high))

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
        ser2.add_action(Action('stop', "foo"))
        ser2.inherits_from(ser1)
        self.assertEqual(ser2.target, NodeSet('127.0.0.1'))
        self.assertEqual(ser2._actions['start'].target, NodeSet('127.0.0.1'))
        self.assertEqual(ser2._actions['stop'].target, NodeSet("foo"))

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
        service.origin = True
        action.status = DONE 
        service.add_action(action)
        service._last_action = 'start'
        service.reset()
        self.assertFalse(service.origin)
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
        act_a = Action('start', command='/bin/true')
        act_b = Action('stop', command='/bin/true')
        act_c = Action('status', command='/bin/true')
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

    def test_prepare_single_service(self):
        """Test prepare without dependencies between services."""
        serv_test = Service('test_service')
        ac_start = Action(name='start', command='/bin/true')
        serv_test.add_action(ac_start)
        serv_test.run('start')
        self.assertTrue(serv_test.origin)
        self.assertEqual(serv_test.status, DONE)

    def test_prepare_one_dependency(self):
        """Test prepare with one dependency."""
        # Define the main service
        serv_test = Service('test_service')
        start = Action(name='start', command='/bin/true')
        start2 = Action(name='start', command='/bin/true')
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
        start = Action(name='start', command='/bin/true')
        start2 = Action(name='start', command='/bin/true')
        start3 = Action(name='start', command='/bin/true')
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

    def test_run_skipped(self):
        """Run a service with empty target is SKIPPED"""
        svc = Service('test_service')
        action = Action('start', target="TEMPNODE", command=":")
        svc.add_action(action)
        action.update_target("TEMPNODE", 'DIF')
        svc.run('start')

        self.assertEqual(action.status, SKIPPED)
        self.assertEqual(svc.status, SKIPPED)

    def test_run_with_skipped_deps(self):
        """Test run with only SKIPPED dependencies"""

        # Define the main service
        serv_test = Service('test_service')
        start = Action(name='start', command='/bin/true')
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

    def test_run_skipped_with_error_deps(self):
        """Test run with ERROR dependencies for a SKIPPED service"""

        # Distant service with empty target: should be skipped
        svc = Service('test_service', target="tempnode[1-2]")
        action = Action('start', command='/bin/true')
        action.inherits_from(svc)
        svc.add_action(action)
        svc.update_target("tempnode[1-2]", 'DIF')

        # A simple dep
        dep = Service('DEP_A')
        dep.add_action(Action('start', command='/bin/false'))

        svc.add_dep(dep)
        svc.run('start')

        self.assertEqual(svc.eval_deps_status(), DEP_ERROR)
        self.assertEqual(dep.status, ERROR)
        self.assertEqual(svc.status, SKIPPED)

    def test_prepare_multilevel_dependencies(self):
        """Test prepare with multiple dependencies at different levels."""
        #Service Arthemis is delcared here
        arth = Service('arthemis')
        arth.desc = 'Sleep five seconds'
        start = Action(name='start', command='/bin/true')
        start2 = Action(name='start', command='/bin/true')
        start3 = Action(name='start', command='/bin/true')
        start4 = Action(name='start', command='/bin/true')
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

        suc = Action(name='start', command='/bin/true')
        suc2 = Action(name='start', command='/bin/true')
        ac_err = Action(name='start', command='/bin/false')

        serv.add_action(suc)
        serv_a.add_action(ac_err)
        serv_b.add_action(suc2)

        serv.add_dep(serv_b)
        serv.add_dep(serv_a, REQUIRE_WEAK)

        serv.run('start')

        self.assertEqual(serv.status, DONE)
        self.assertEqual(serv_a.status, ERROR)
        self.assertEqual(serv_b.status, DONE)

    def test_prepare_require_strong(self):
        """Test strong require dependency error."""
        serv = Service('BASE')
        serv_a = Service('DEP_A')
        serv_b = Service('DEP_B')

        ac_suc = Action(name='start', command='/bin/true')
        ac_suc2 = Action(name='start', command='/bin/true')
        ac_err = Action(name='start', command='/bin/false')

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

        ac_suc = Action(name='start', command='/bin/true')
        ac_suc2 = Action(name='start', command='/bin/true')
        ac_err = Action(name='start', command='/bin/false')
        ac_err2 = Action(name='start', command='dlvlfvlf')

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

        ac_suc = Action(name='start', command='/bin/true')
        ac_suc2 = Action(name='start', command='/bin/true')
        ac_suc3 = Action(name='start', command='/bin/true')
        ac_tim = Action(name='start', command='sleep 3', timeout=0.3)

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
        self.assertEqual(serv_ok_warnings.status, DONE)
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

        act_suc = Action(name='start', command='/bin/true')
        act_suc2 = Action(name='start', command='/bin/true')
        act_suc3 = Action(name='start', command='/bin/true')
        act_suc4 = Action(name='start', command='/bin/true')
        act_suc5 = Action(name='start', command='/bin/true')
        act_status_failed = Action(name='status', command='/bin/false')
        act_status = Action(name='status', command='/bin/true')

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
        self.assertEqual(serv_a.status, DONE)
        
    def test_prepare_delayed_action(self):
        """Test prepare Service with a delayed action"""
        serv = Service('DELAYED_SERVICE')
        act = Action(name='start', command='/bin/true', delay=1)
        serv.add_action(act)
        serv.run('start')
        self.assertEqual(serv.status, DONE)
        self.assert_near(1.0, 0.3, act.duration)

    def test_prepare_multiple_delay(self):
        '''Test prepare with dependencies and multiple delays'''
        serv = Service('BASE_DELAYED')
        serv_a = Service('A_NOT_DELAYED')
        serv_b = Service('B_DELAYED')
        serv_c = Service('C_DELAYED')
        act_a = Action(name='start', command='/bin/true')
        act_serv = Action(name='start', command='/bin/true', delay=0.3)
        act_b = Action(name='start', command='/bin/true', delay=0.3)
        act_c = Action(name='start', command='/bin/true', delay=0.5)
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
        self.assert_near(0.3, 0.2, act_serv.duration)
        self.assertEqual(serv_a.status, DONE)
        self.assert_near(0.0, 0.2, act_a.duration)
        self.assertEqual(serv_b.status, DONE)
        self.assert_near(0.3, 0.2, act_b.duration)
        self.assertEqual(serv_c.status, DONE)
        self.assert_near(0.5, 0.2, act_c.duration)

    def test_run_partial_deps(self):
        """Test stop algorithm as soon as the calling point is done."""
        serv = Service('NOT_CALLED')
        serv_a = Service('CALLING_POINT')
        serv_b = Service('SERV_1')
        serv_c = Service('SERV_2')
        act_suc = Action('start', command='/bin/true')
        act_suc2 = Action('start', command='/bin/true')
        act_suc3 = Action('start', command='/bin/true')
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
        act_start = Action('start', command='/bin/true')
        act_status = Action('status', command='/bin/true')
        act_start.add_dep(target=act_status)
        serv.add_actions(act_start, act_status)
        serv.run('start')
        self.assertEqual(serv.status, DONE)
        self.assertFalse(act_start.duration)
        self.assertTrue(act_status.duration)
        
    def test_run_action_with_failed_subaction(self):
        """Test action running a failed sub action (start->status)"""
        serv = Service('BASE')
        act_start = Action('start', command='/bin/true')
        act_status_fail = Action('status', command='/bin/false')
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

        act_start1 = Action("start", command="/bin/true")
        act_start2 = Action("start", command="/bin/false")
        act_start3 = Action("start", command="/bin/true")
        act_start4 = Action("start", command="/bin/true")
        act_sta = Action("status", command="/bin/true")
        act_sta_fai = Action("status", command="/bin/false")

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
        stop = Action('stop', command='/bin/true')
        ser.add_action(stop)
        ser.run('stop')
        self.assertEqual(ser.status, DONE)
        self.assertTrue(stop.duration)

    def test_run_reverse_with_dependencies(self):
        ser = Service('REVERSE_BASE')
        ser_dep = Service('REVERSE_DEP')
        ser.algo_reversed = True
        ser_dep.algo_reversed = True
        stop1 = Action('stop', command='/bin/true')
        stop2 = Action('stop', command='/bin/true')
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
        stop = Action(name='stop', command='/bin/true')
        stop2 = Action(name='stop', command='/bin/true')
        stop3 = Action(name='stop', command='/bin/true')
        stop4 = Action(name='stop', command='/bin/true')
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
        start_s1 = Action('start', command='/bin/true')
        stop_s1 = Action('stop', command='/bin/true')
        s1.add_actions(start_s1, stop_s1)
        # Actions S2
        start_s2 = Action('start', command='/bin/true')
        stop_s2 = Action('stop', command='/bin/true')
        s2.add_actions(start_s2, stop_s2)
        # Actions S3
        start_s3 = Action('start', command='/bin/false')
        stop_s3 = Action('stop', command='/bin/false')
        s3.add_actions(start_s3, stop_s3)
        # Actions S4
        start_s4 = Action('start', command='/bin/true')
        stop_s4 = Action('stop', command='/bin/true')
        s4.add_actions(start_s4, stop_s4)
        # Actions I1
        start_s5 = Action('start', command='/bin/true')
        stop_s5 = Action('stop', command='/bin/true')
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
        s1.add_action(Action('start', command='/bin/true'))
        s1.add_action(Action('status', command='/bin/true'))
        s2 = Service("2")
        s2.add_action(Action('start', command='/bin/true'))
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
        s3.add_action(Action('start', command='/bin/true'))
        s3.add_action(Action('status', command='/bin/true'))
        s3.add_dep(s2)
        s3.run('status')
        self.assertEqual(s1.status, DONE)
        self.assertEqual(s2.status, MISSING)
        self.assertEqual(s3.status, DONE)

    def test_double_deps(self):
        """Test run() with service with a special double deps"""

        # Was a bug when you got:

        # _src -> otherotherother -> final
        # _src -> source -> inter -> final
        #
        # inter was not run

        svc1 = Service("final")
        svc1.add_action(Action('start', command='/bin/true'))

        svc2 = Service("inter")
        svc2.add_action(Action('start', command='/bin/true'))
        svc2.add_dep(svc1)

        svc3 = Service("source")
        svc3.add_action(Action('start', command='/bin/true'))
        svc3.add_dep(svc1)
        svc3.add_dep(svc2)

        svc4 = Service("otherotherother")
        svc4.add_action(Action('start', command='/bin/true'))
        svc4.add_dep(svc1)

        src = Service("_src")
        src.add_action(Action('start', command=':'))
        src.add_dep(svc4)
        src.add_dep(svc3)

        src.run('start')

        self.assertEqual(svc1.status, DONE)
        self.assertEqual(svc2.status, DONE)
        self.assertEqual(svc3.status, DONE)
        self.assertEqual(svc4.status, DONE)

    def test_filter_dep_no_error(self):
        """test FILTER dependency without error"""
        svc1 = Service('first')
        svc1.add_action(Action('start', command='/bin/true', target=HOSTNAME))

        svc2 = Service('second')
        svc2.add_action(Action('start', command='/bin/true', target=HOSTNAME))
        svc2.add_dep(svc1, sgth=FILTER)

        svc2.run('start')

        self.assertEqual(svc1.status, DONE)
        self.assertEqual(svc2.status, DONE)

    def test_filter_dep_one_error(self):
        """error nodes are propagated along 'filter' dependencies"""
        svc1 = Service('first')
        svc1.add_action(Action('start', command='false', target=HOSTNAME))

        svc2 = Service('second')
        svc2.add_action(Action('start', command='true', target=HOSTNAME))
        svc2.add_dep(svc1, sgth=FILTER)

        svc2.run('start')

        self.assertEqual(svc1.status, ERROR)
        self.assertEqual(svc2.status, SKIPPED)

    def test_filter_dep_timeout(self):
        """timeout nodes are propagated along 'filter' dependencies"""
        svc1 = Service('first')
        svc1.add_action(Action('start', command='sleep 1', target=HOSTNAME,
                               timeout=0.1))

        svc2 = Service('second')
        svc2.add_action(Action('start', command='true', target=HOSTNAME))
        svc2.add_dep(svc1, sgth=FILTER)

        svc2.run('start')

        self.assertEqual(svc1.status, TIMEOUT)
        self.assertEqual(svc2.status, SKIPPED)

    def test_filter_dep_error_propagation(self):
        """error nodes are propagated along 'filter' dependencies (one node)"""
        svc1 = Service('first')
        tgt = '%s,fakenode' % HOSTNAME
        svc1.add_action(Action('start', command='true', target=tgt))

        svc2 = Service('second')
        svc2.add_action(Action('start', command='true', target=HOSTNAME))
        svc2.add_dep(svc1, sgth=FILTER)

        svc2.run('start')

        self.assertEqual(svc1.status, ERROR)
        self.assertEqual(svc2.status, DONE)

    def test_filter_error_no_action(self):
        """
        propagation along 'filter' dependencies works if action names mismatch
        """
        svc1 = Service('first')
        svc1.add_action(Action('start', command='false', target=HOSTNAME))

        svc2 = Service('second')
        svc2.add_action(Action('other', command='true', target=HOSTNAME))
        svc2.add_dep(svc1, sgth=FILTER)

        svc2.run('start')

        self.assertEqual(svc1.status, ERROR)
        self.assertEqual(svc2.status, MISSING)

    def test_filter_two_deps(self):
        """error nodes are send even with multiple filter deps"""
        svc1 = Service('top')
        tgt = '%s,fakenode' % HOSTNAME
        svc1.add_action(Action('start', command='true', target=tgt))

        svc2 = Service('bottom1')
        svc2.add_action(Action('start', command='true', target=HOSTNAME))
        svc2.add_dep(svc1, sgth=FILTER)

        svc3 = Service('bottom2')
        svc3.add_action(Action('start', command='true', target='fakenode'))
        svc3.add_dep(svc1, sgth=FILTER)

        svc4 = Service('src')
        svc4.add_dep(svc2)
        svc4.add_dep(svc3)
        svc4.run('start')

        self.assertEqual(svc1.status, ERROR)
        self.assertEqual(svc2.status, DONE)
        self.assertEqual(svc3.status, SKIPPED)
        self.assertEqual(svc4.status, MISSING)

    def test_filter_mixed(self):
        """test filter and regular deps works fine together"""
        svc1 = Service('top1')
        tgt = '%s,fakenode' % HOSTNAME
        svc1.add_action(Action('start', command='true', target=tgt))

        svc2 = Service('top2')
        svc2.add_action(Action('start', command='true', target=HOSTNAME))

        svc3 = Service('bottom')
        svc3.add_action(Action('start', command='true', target='fakenode'))
        svc3.add_dep(svc1, sgth=REQUIRE)
        svc3.add_dep(svc2, sgth=FILTER)

        svc3.run('start')

        self.assertEqual(svc1.status, ERROR)
        self.assertEqual(svc2.status, DONE)
        self.assertEqual(svc3.status, DEP_ERROR)

    def test_filter_no_target(self):
        """service without target are not filtered"""
        svc1 = Service('top')
        svc1.add_action(Action('start', command='false'))

        svc2 = Service('bottom')
        svc2.add_action(Action('start', command='true'))
        svc2.add_dep(svc1, sgth=FILTER)

        svc2.run('start')

        self.assertEqual(svc1.status, ERROR)
        self.assertEqual(svc2.status, DONE)

    def test_filter_mix_no_target(self):
        """service without target do not filter service with target"""
        svc1 = Service('top')
        svc1.add_action(Action('start', command='false'))

        svc2 = Service('bottom')
        svc2.add_action(Action('start', command='true', target='localhost'))
        svc2.add_dep(svc1, sgth=FILTER)

        svc2.run('start')

        self.assertEqual(svc1.status, ERROR)
        self.assertEqual(svc2.status, DONE)

    def test_skip(self):
        """Test skip method for services"""
        srv = Service('skipped')
        srv.add_action(Action('start', target=NodeSet('foo'),
                              command='/bin/true'))
        srv.skip()
        self.assertTrue(srv._actions['start'].to_skip())


class ServiceFromDictTest(TestCase):
    '''This class tests Service.fromdict()'''

    def test_fromdict1(self):
        '''Test instanciate a service from a dictionnary'''
        ser = Service('S1')
        ser.fromdict(
            {
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
        )
        self.assertTrue(ser)
        self.assertEqual(ser.name, 'S1')
        self.assertEqual(ser.desc, 'I am the service S1')
        self.assertEqual(ser.target, NodeSet('localhost'))
        self.assertEqual(len(ser.variables), 2)
        self.assertTrue('var1' in ser.variables)
        self.assertTrue('var2' in ser.variables)

    def test_fromdict2(self):
        '''
        Test instanciate a service from a dictionnary with dependant actions
        '''
        ser = Service('S1')
        ser.fromdict(
            {
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
        )
        self.assertTrue(ser)
        self.assertEqual(len(ser._actions), 3)
        self.assertTrue('start' in ser._actions)
        self.assertTrue('stop' in ser._actions)
        self.assertTrue('status' in ser._actions)
        self.assertTrue(ser._actions['start'].has_parent_dep('status'))

    def test_service_with_actions_with_one_decl(self):
        """create a service with two actions with comma declaration"""

        svc = Service('foo')
        svc.fromdict(
            {
                'actions':
                {
                    'start,stop':
                    {
                        'cmd': 'service foo %ACTION'
                    },
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

        svc = Service('foo')
        svc.fromdict(
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
        )
        self.assertTrue(svc)
        self.assertEqual(len(svc._actions), 2)
        self.assertTrue('foo1' in svc._actions)
        self.assertTrue('foo2' in svc._actions)
        self.assertEqual(svc._actions['foo1'].command,
                         'service foo %ACTION')
        self.assertEqual(svc._actions['foo2'].command,
                         'service foo %ACTION')

    def test_delay_to_action(self):
        """
        test if the delay defined in the service dict is correctly given to
        the action
        """
        svc = Service('foo')
        svc.fromdict(
            {
                'name': 'foo',
                'delay': 1,
                'actions':
                {
                    'wait':
                    {
                        'cmd': 'service wait %ACTION'
                    },
                }
            }
        )
        self.assertEqual(svc._actions['wait'].delay, 1)

    def test_retry_to_action(self):
        """
        test if the retry defined in the service dict is correctly given to
        the action
        """
        svc = Service('foo')
        svc.fromdict(
            {
                'name': 'foo',
                'retry': 1,
                'actions':
                {
                    'wait':
                    {
                        'cmd': 'service wait %ACTION'
                    },
                }
            }
        )
        self.assertEqual(svc._actions['wait'].maxretry, 1)
        self.assertEqual(svc._actions['wait'].tries, 0)

    def test_resolve_target_from_parent(self):
        """resolve action target using variable declared in parent service"""
        # 'target' property is resolved very early and not in resolve_all()
        data = {
            'variables': {
                'targets': 'foo'
            },
            'actions': {
                'start': {
                    'target': '%targets',
                    'cmd': '/bin/true',
                }
            }
        }
        svc = Service('svc')
        svc.fromdict(data)
        self.assertEqual(str(svc._actions['start'].target), 'foo')

    def test_resolve_all(self):
        """Test variable resolution in resolve_all()"""
        srv = Service('svc1')
        srv.add_var('label', "I am a service")
        srv.fromdict({
                      'desc': "%label",
                      'actions': {
                           'start': {
                               'cmd': 'service foo %ACTION'
                           },
                      }
                    })
        srv.resolve_all()
        self.assertEqual(srv.desc, "I am a service")
        self.assertEqual(srv._actions['start'].command, "service foo start")
