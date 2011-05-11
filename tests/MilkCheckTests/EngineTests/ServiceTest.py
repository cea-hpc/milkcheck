# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This modules defines the tests cases targeting the Action and Service objects.
"""
from unittest import TestCase

# Classes
from MilkCheck.Engine.Service import Service
from MilkCheck.Engine.Action import Action

# Exceptions
from MilkCheck.Engine.Service import ActionAlreadyReferencedError
from MilkCheck.Engine.Service import ActionNotFoundError

# Symbols
from MilkCheck.Engine.BaseEntity import NO_STATUS, DONE, TIMED_OUT, ERROR
from MilkCheck.Engine.BaseEntity import TOO_MANY_ERRORS, WAITING_STATUS
from MilkCheck.Engine.BaseEntity import DONE_WITH_WARNINGS 
from MilkCheck.Engine.Dependency import CHECK, REQUIRE, REQUIRE_WEAK

class ActionTest(TestCase):
    """Define the unit tests for the object action."""
    
    def test_action_instanciation(self):
        """Test instanciation of an action."""
        action = Action('start')
        self.assertNotEqual(action, None, 'should be none')
        self.assertEqual(action.name, 'start', 'wrong name')
        action = Action(name='start', target='fortoy5', command='/bin/true')
        self.assertEqual(action.target, 'fortoy5', 'wrong target')
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
        
    def test_update_status(self):
        """TODO"""
        pass
        
class ServiceTest(TestCase):
    """Define the unit tests for the object service."""
    def test_service_instanciation(self):
        """Test instanciation of a service."""
        service = Service('brutus')
        self.assertNotEqual(service, None, 'should be none')
        self.assertEqual(service.name, 'brutus', 'wrong name')

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
        act_a = Action('start', 'localhost', '/bin/true')
        act_b = Action('stop', 'localhost', '/bin/true')
        act_c = Action('status', 'localhost', '/bin/true')
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

        start = Action('start', 'localhost', '/bin/true')
        service.add_action(start)
        self.assertRaises(ActionNotFoundError, service.last_action)
        service.prepare('start')
        self.assertTrue(service.last_action())
        self.assertTrue(service.last_action() is start)

    def test_prepare_error(self):
        """Test prepare exception if action is not found."""
        # Single service
        service = Service("brutus")
        service.add_action(Action('start'))
        self.assertRaises(ActionNotFoundError,
            service.prepare, 'status')

        # Service with dependencies but one level
        serv_a = Service('A')
        serv_b = Service('B')
        serv_a.add_action(Action('start'))
        service.add_dep(serv_a)
        service.add_dep(serv_b)
        self.assertRaises(ActionNotFoundError,
            service.prepare)

        #Service with dependencies and multiple levels
        serv_b.add_action(Action('start'))
        serv_c = Service('C')
        serv_a.add_dep(serv_c, CHECK)
        self.assertRaises(ActionNotFoundError,
            service.prepare)

    def test_prepare_single_service(self):
        """Test prepare without dependencies between services."""
        serv_test = Service('test_service')
        ac_start = Action(name='start', target='localhost', command='/bin/true')
        serv_test.add_action(ac_start)
        serv_test.run('start')
        self.assertEqual(serv_test.status, DONE)

    def test_prepare_one_dependency(self):
        """Test prepare with one dependency."""
        # Define the main service
        serv_test = Service('test_service')
        start = Action(name='start', target='localhost', command='/bin/true')
        start2 = Action(name='start', target='localhost', command='/bin/true')
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
        start = Action(name='start', target='localhost', command='/bin/true')
        start2 = Action(name='start', target='localhost', command='/bin/true')
        start3 = Action(name='start', target='localhost', command='/bin/true')
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

    def test_prepare_multilevel_dependencies(self):
        """Test prepare with multiple dependencies at different levels."""
        #Service Arthemis is delcared here
        arth = Service('arthemis')
        arth.desc = 'Sleep five seconds'
        start = Action(name='start', target='localhost', command='/bin/true')
        start2 = Action(name='start', target='localhost', command='/bin/true')
        start3 = Action(name='start', target='localhost', command='/bin/true')
        start4 = Action(name='start', target='localhost', command='/bin/true')
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

        suc = Action(name='start', target='localhost', command='/bin/true')
        suc2 = Action(name='start', target='localhost', command='/bin/true')
        ac_err = Action(name='start', target='localhost', command='/bin/false')

        serv.add_action(suc)
        serv_a.add_action(ac_err)
        serv_b.add_action(suc2)

        serv.add_dep(serv_b)
        serv.add_dep(serv_a, REQUIRE_WEAK)

        serv.run('start')

        self.assertEqual(serv.status, DONE_WITH_WARNINGS)
        self.assertEqual(serv_a.status, TOO_MANY_ERRORS)
        self.assertEqual(serv_b.status, DONE)

    def test_prepare_require_strong(self):
        """Test strong require dependency error."""
        serv = Service('BASE')
        serv_a = Service('DEP_A')
        serv_b = Service('DEP_B')

        ac_suc = Action(name='start', target='localhost', command='/bin/true')
        ac_suc2 = Action(name='start', target='localhost', command='/bin/true')
        ac_err = Action(name='start', target='localhost', command='/bin/false')

        serv.add_action(ac_suc)
        serv_a.add_action(ac_err)
        serv_b.add_action(ac_suc2)

        serv.add_dep(serv_b)
        serv.add_dep(serv_a)

        serv.run('start')

        self.assertEqual(serv.status, ERROR)
        self.assertEqual(serv_a.status, TOO_MANY_ERRORS)
        self.assertEqual(serv_b.status, DONE)

    def test_prepare_errors_same_level(self):
        """Test prepare behaviour with two errors at the same level"""
        serv = Service('BASE')
        serv_a = Service('DEP_A')
        serv_b = Service('DEP_B')
        serv_c = Service('DEP_C')

        ac_suc = Action(name='start', target='localhost', command='/bin/true')
        ac_suc2 = Action(name='start', target='localhost', command='/bin/true')
        ac_err = Action(name='start', target='localhost', command='/bin/false')
        ac_err2 = Action(name='start', target='localhost', command='dlvlfvlf')

        serv.add_action(ac_suc)
        serv_a.add_action(ac_suc2)
        serv_b.add_action(ac_err)
        serv_c.add_action(ac_err2)

        serv.add_dep(serv_a)
        serv_a.add_dep(serv_b)
        serv_a.add_dep(serv_c)

        serv.run('start')

        self.assertEqual(serv.status, ERROR)
        self.assertEqual(serv_a.status, ERROR)
        self.assertEqual(serv_b.status, TOO_MANY_ERRORS)
        self.assertEqual(serv_c.status, TOO_MANY_ERRORS)
        
    def test_prepare_with_multiple_require_errors(self):
        """Test multiple require dependencies errors at different levels."""
        serv_base_error = Service('A')
        serv_ok_warnings = Service('B')
        serv_error = Service('C')
        serv_timed_out = Service('D')

        ac_suc = Action(name='start', target='localhost', command='/bin/true')
        ac_suc2 = Action(name='start', target='localhost', command='/bin/true')
        ac_suc3 = Action(name='start', target='localhost', command='/bin/true')
        ac_tim = Action(name='start', target='localhost',
                     command='sleep 3', timeout=2)

        serv_base_error.add_action(ac_suc)
        serv_ok_warnings.add_action(ac_suc2)
        serv_error.add_action(ac_suc3)
        serv_timed_out.add_action(ac_tim)

        serv_base_error.add_dep(serv_ok_warnings)
        serv_base_error.add_dep(serv_error)
        serv_ok_warnings.add_dep(serv_timed_out, REQUIRE_WEAK)
        serv_error.add_dep(serv_timed_out)

        serv_base_error.run('start')

        self.assertEqual(serv_base_error.status, ERROR)
        self.assertEqual(serv_ok_warnings.status, DONE_WITH_WARNINGS)
        self.assertEqual(serv_error.status, ERROR)
        self.assertEqual(serv_timed_out.status, TIMED_OUT)

    def test_prepare_multiple_errors(self):
        """Test prepare with check and require deps with errors."""
        serv_a = Service('BASE')
        serv_b = Service('DEP_B')
        serv_c = Service('DEP_C')
        serv_d = Service('DEP_D')
        serv_x = Service('DEP_VX')
        serv_k = Service('DEP_K')

        act_suc = Action(name='start', target='localhost', command='/bin/true')
        act_suc2 = Action(name='start', target='localhost', command='/bin/true')
        act_suc3 = Action(name='start', target='localhost', command='/bin/true')
        act_suc4 = Action(name='start', target='localhost', command='/bin/true')
        act_suc5 = Action(name='start', target='localhost', command='/bin/true')
        act_status_failed = Action(name='status', target='localhost',
            command='/bin/false')
        act_status = Action(name='status', target='localhost',
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
        self.assertEqual(serv_k.status, TOO_MANY_ERRORS)
        self.assertEqual(serv_c.status, ERROR)
        self.assertEqual(serv_b.status, DONE)
        self.assertEqual(serv_x.status, DONE)
        self.assertEqual(serv_a.status, DONE_WITH_WARNINGS)
        
    def test_prepare_delayed_action(self):
        """Test prepare Service with a delayed action"""
        serv = Service('DELAYED_SERVICE')
        act_suc = ac_suc = Action(name='start',
                    target='localhost', command='/bin/true', delay=5)
        serv.add_action(act_suc)
        serv.run('start')
        self.assertEqual(serv.status, DONE)
        action_done = serv.last_action()
        self.assertTrue(5 < action_done.duration and action_done.duration < 6)

    def test_prepare_multiple_delay(self):
        '''Test prepare with dependencies and multiple delay'''
        serv = Service('BASE_DELAYED')
        serv_a = Service('A_NOT_DELAYED')
        serv_b = Service('B_DELAYED')
        serv_c = Service('C_DELAYED')
        act_a = Action(name='start',
                    target='localhost', command='/bin/true')
        act_serv = Action(name='start',
                    target='localhost', command='/bin/true', delay=1)
        act_b = Action(name='start',
                    target='localhost', command='/bin/true', delay=1)
        act_c = Action(name='start',
                    target='localhost', command='/bin/true', delay=2)
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
        self.assertTrue(0.8 < action.duration and action.duration < 1.4)
        self.assertEqual(serv_a.status, DONE)
        action = serv_a.last_action()
        self.assertTrue(0 < action.duration and action.duration < 0.5)
        self.assertEqual(serv_b.status, DONE)
        action = serv_b.last_action()
        self.assertTrue(0.8 < action.duration and action.duration < 1.4)
        self.assertEqual(serv_c.status, DONE)
        action = serv_c.last_action()
        self.assertTrue(1.8 < action.duration and action.duration < 2.4)

    def test_run_partial_deps(self):
        """Test stop algorithm as soon as the calling point is done."""
        serv = Service('NOT_CALLED')
        serv_a = Service('CALLING_POINT')
        serv_b = Service('SERV_1')
        serv_c = Service('SERV_2')
        act_suc = Action('start', 'localhost', '/bin/true')
        act_suc2 = Action('start', 'localhost', '/bin/true')
        act_suc3 = Action('start', 'localhost', '/bin/true')
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
        act_start = Action('start', 'localhost', '/bin/true')
        act_status = Action('status', 'localhost', '/bin/true')
        act_start.add_dep(target=act_status)
        serv.add_actions(act_start, act_status)
        serv.run('start')
        self.assertEqual(serv.status, DONE)
        self.assertFalse(act_start.duration)
        self.assertTrue(act_status.duration)
        
    def test_run_action_with_failed_subaction(self):
        """Test action running a failed sub action (start->status)"""
        serv = Service('BASE')
        act_start = Action('start', 'localhost', '/bin/true')
        act_status_fail = Action('status', 'localhost', '/bin/false')
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

        act_start1 = Action("start", "localhost", "/bin/true")
        act_start2 = Action("start", "localhost", "/bin/false")
        act_start3 = Action("start", "localhost", "/bin/true")
        act_start4 = Action("start", "localhost", "/bin/true")
        act_sta = Action("status", "localhost", "/bin/true")
        act_sta_fai = Action("status", "localhost", "/bin/false")

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
        self.assertEqual(zombie_one.status, TOO_MANY_ERRORS)
        self.assertEqual(zombie_two.status, DONE)
        self.assertEqual(nemesis.status, ERROR)
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
        stop = Action('stop', 'localhost', '/bin/true')
        ser.add_action(stop)
        ser.run('stop')
        self.assertEqual(ser.status, DONE)
        self.assertTrue(stop.duration)

    def test_run_reverse_with_dependencies(self):
        ser = Service('REVERSE_BASE')
        ser_dep = Service('REVERSE_DEP')
        ser.algo_reversed = True
        ser_dep.algo_reversed = True
        stop1 = Action('stop', 'localhost', '/bin/true')
        stop2 = Action('stop', 'localhost', '/bin/true')
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
        stop = Action(name='stop', target='localhost', command='/bin/true')
        stop2 = Action(name='stop', target='localhost', command='/bin/true')
        stop3 = Action(name='stop', target='localhost', command='/bin/true')
        stop4 = Action(name='stop', target='localhost', command='/bin/true')
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