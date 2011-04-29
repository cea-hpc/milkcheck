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
from MilkCheck.Engine.BaseEntity import NO_STATUS, RUNNING, TIMED_OUT, ERROR
from MilkCheck.Engine.BaseEntity import TOO_MANY_ERRORS
from MilkCheck.Engine.BaseEntity import RUNNING_WITH_WARNINGS
from MilkCheck.Engine.Dependency import CHECK, REQUIRE, REQUIRE_WEAK

class ActionTest(TestCase):
    """Define the unit tests for the object action."""
    
    def test_action_instanciation(self):
        """Test instanciation of an action."""
        action = Action("start")
        self.assertNotEqual(action, None, "should be none")
        self.assertEqual(action.name, "start", "wrong name")
        action = Action(name="start", target="fortoy5", command="/bin/true")
        self.assertEqual(action.target, "fortoy5", "wrong target")
        self.assertEqual(action.command, "/bin/true", "wrong command")
        action = Action(name="start", target="fortoy5", command="/bin/true",
                    timeout=10, delay=5)
        self.assertEqual(action.timeout, 10, "wrong timeout")
        self.assertEqual(action.delay, 5, "wrong delay")
        
    def test_has_too_many_errors(self):
        """Test the method has_too_many_errors."""
        action = Action(name="start", target="aury[12,13,21]",
                    command="/bin/false")
        action.errors = 2
        service = Service("test_service")
        service.add_action(action)
        service.prepare("start")
        service.resume()
        last_action = service.last_action()
        self.assertTrue(last_action.has_too_many_errors())
        
        act_test = Action(name="test", target="fortoy5", command="/bin/true")
        service.add_action(act_test)
        service.prepare("test")
        service.resume()
        self.assertFalse(action.has_too_many_errors())
        
    def test_has_timed_out(self):
        """Test has_timed_ou_method."""
        action = Action(name="start", target="localhost",
                    command="sleep 3", timeout=2)
        service = Service("test_service")
        service.add_action(action)
        service.prepare("start")
        service.resume()
        last_action = service.last_action()
        self.assertTrue(last_action.has_timed_out())
        
    def test_set_retry(self):
        """Test retry assignement"""
        action =  Action(name="start", target="localhost", command="sleep 3")
        self.assertRaises(AssertionError, action.set_retry, 5)
        action =  Action(name="start", target="localhost", command="sleep 3",
                    delay=3)
        action.retry = 5
        self.assertEqual(action.retry, 5)
        
class ServiceTest(TestCase):
    """Define the unit tests for the object service."""
    def test_service_instanciation(self):
        """Test instanciation of a service."""
        service = Service("brutus")
        self.assertNotEqual(service, None, "should be none")
        self.assertEqual(service.name, "brutus", "wrong name")
        
    def test_add_action(self):
        """Test add_action's behaviour."""
        service = Service("brutus")
        service.add_action(Action("start"))
        self.assertTrue(service.has_action("start"))
        self.assertRaises(ActionAlreadyReferencedError,
                service.add_action,Action("start"))
        self.assertRaises(TypeError,
                service.add_action,None)
                
    def test_add_actions(self):
        """Test the possibility to add multiple actions at the same time"""
        service = Service("SERV")
        act_a = Action("start", "localhost", "/bin/true")
        act_b = Action("stop", "localhost", "/bin/true")
        act_c = Action("status", "localhost", "/bin/true")
        service.add_actions(act_a, act_b, act_c)
        self.assertTrue(service.has_action("start"))
        self.assertTrue(service.has_action("stop"))
        self.assertTrue(service.has_action("status"))
        
    def test_remove_action(self):
        """Test remove_action behaviour."""
        service = Service("brutus")
        service.add_action(Action("start"))
        service.remove_action("start")
        self.assertFalse(service.has_action("start"))
        self.assertRaises(ActionNotFoundError,
            service.remove_action, "start")
    
    def test_last_action(self):
        """Test last_action method behaviour."""
        service = Service("henry")
        self.assertRaises(ActionNotFoundError, service.last_action)
        
        start = Action("start")
        start.target = "aury12"
        start.command = "hostname"
        service.add_action(start)
        self.assertRaises(ActionNotFoundError, service.last_action)
        
        service.prepare("start")
        self.assertTrue(service.last_action())
    
    def test_add_dep(self):
        """
        Test that you are not allowed to add an internal dependency
        to a service
        """
        ser = Service("SERVICE")
        self.assertRaises(AssertionError, ser.add_dep,
            Service("A"), CHECK, True ,True)
      
    def test_prepare_error(self):
        """Test prepare exception if action is not found."""
        # Single service
        service = Service("brutus")
        service.add_action(Action('start'))
        self.assertRaises(ActionNotFoundError,
            service.prepare, "status")
        
        # Service with dependencies but one level
        serv_a = Service("A")
        serv_b = Service("B")
        serv_a.add_action(Action("start"))
        service.add_dep(serv_a)
        service.add_dep(serv_b)
        self.assertRaises(ActionNotFoundError,
            service.prepare)
            
        #Service with dependencies and multiple levels
        serv_b.add_action(Action("start"))
        serv_c = Service("C")
        serv_a.add_dep(serv_c, CHECK)
        self.assertRaises(ActionNotFoundError,
            service.prepare)
            
    def test_prepare_single_service(self):
        """Test prepare without dependencies between services."""
        serv_test = Service("test_service")
        ac_start = Action(name="start", target="localhost", command="/bin/true")
        serv_test.add_action(ac_start)
        serv_test.prepare("start")
        serv_test.resume()
        self.assertEqual(serv_test.status, RUNNING)
        
    def test_prepare_one_dependency(self):
        """Test prepare with one dependency."""
        # Define the main service
        serv_test = Service("test_service")
        ac_start = Action(name="start", target="localhost", command="/bin/true")
        serv_test.add_action(ac_start)
        
        # Define the single dependency of the main service
        serv_dep = Service("dependency")
        serv_dep.add_action(ac_start)
        serv_test.add_dep(serv_dep)
        
        # Start preparing of the base service
        serv_test.prepare("start")
        serv_test.resume()
        self.assertEqual(serv_test.status, RUNNING)
        self.assertEqual(serv_dep.status, RUNNING)
        
    def test_prepare_several_dependencies(self):
        """Test prepare with several dependencies at the same level."""
        # Define the main service
        serv_test = Service("test_service")
        ac_start = Action(name="start", target="localhost", command="/bin/true")
        serv_test.add_action(ac_start)
        
        # Define the dependency DEP_A 
        serv_depa = Service("DEP_A")
        serv_depa.add_action(ac_start)
        
        # Define the dependency DEP_B
        serv_depb = Service("DEP_B")
        serv_depb.add_action(ac_start)
        
        serv_test.add_dep(serv_depa)
        serv_test.add_dep(serv_depb)
    
        serv_test.prepare("start")
        serv_test.resume()
        self.assertEqual(serv_test.status, RUNNING)
        self.assertEqual(serv_depa.status, RUNNING)
        self.assertEqual(serv_depb.status, RUNNING)
        
    def test_prepare_multilevel_dependencies(self):
        """Test prepare with multiple dependencies at different levels."""
        #Service Arthemis is delcared here
        arth = Service("arthemis")
        arth.desc = "Sleep five seconds"
        ac_start = Action(name="start", target="localhost", command="/bin/true")
        arth.add_action(ac_start)
        
        # Service Chiva is declared here
        chiva = Service("chiva")
        chiva.desc = "List all processes in details"
        chiva.add_action(ac_start)
        chiva.add_dep(arth)
        
        # Service Dyonisos is declared here
        dion = Service("dionysos")
        dion.desc = "Perform tree on directory specified"
        dion.add_action(ac_start)
        dion.add_dep(arth)
        
        # Service Brutus is declared here
        brut = Service("brutus")
        brut.desc = "Wanna sleep all the time"
        brut.add_action(ac_start)
        
        brut.add_dep(chiva)
        brut.add_dep(dion)
        
        brut.prepare("start")
        brut.resume()
        self.assertEqual(arth.status, RUNNING)
        self.assertEqual(chiva.status, RUNNING)
        self.assertEqual(dion.status, RUNNING)
        self.assertEqual(brut.status, RUNNING)
        
    def test_prepare_require_weak(self):
        """Test weak require dependency error."""
        serv = Service("BASE")
        serv_a = Service("DEP_A")
        serv_b = Service("DEP_B")
        
        ac_suc = Action(name="start", target="localhost", command="/bin/true")
        ac_err = Action(name="start", target="localhost", command="/bin/false")
        
        serv.add_action(ac_suc)
        serv_a.add_action(ac_err)
        serv_b.add_action(ac_suc)
        
        serv.add_dep(serv_b)
        serv.add_dep(serv_a, REQUIRE_WEAK)
        
        serv.prepare("start")
        serv.resume()
        
        self.assertEqual(serv.status, RUNNING_WITH_WARNINGS)
        self.assertEqual(serv_a.status, TOO_MANY_ERRORS)
        self.assertEqual(serv_b.status, RUNNING)
        
    def test_prepare_require_strong(self):
        """Test strong require dependency error."""
        serv = Service("BASE")
        serv_a = Service("DEP_A")
        serv_b = Service("DEP_B")
        
        ac_suc = Action(name="start", target="localhost", command="/bin/true")
        ac_err = Action(name="start", target="localhost", command="/bin/false")
        
        serv.add_action(ac_suc)
        serv_a.add_action(ac_err)
        serv_b.add_action(ac_suc)
        
        serv.add_dep(serv_b)
        serv.add_dep(serv_a)
        
        serv.prepare("start")
        serv.resume()
        
        self.assertEqual(serv.status, ERROR)
        self.assertEqual(serv_a.status, TOO_MANY_ERRORS)
        self.assertEqual(serv_b.status, RUNNING)
   
    def test_prepare_errors_same_level(self):
        """Test prepare behaviour with two errors at the same level"""
        serv = Service("BASE")
        serv_a = Service("DEP_A")
        serv_b = Service("DEP_B")
        serv_c = Service("DEP_C")
        
        ac_suc = Action(name="start", target="localhost", command="/bin/true")
        ac_err = Action(name="start", target="localhost", command="/bin/false")
        ac_err2 = Action(name="start", target="localhost", command="dlvlfvlf")
        
        serv.add_action(ac_suc)
        serv_a.add_action(ac_suc)
        serv_b.add_action(ac_err)
        serv_c.add_action(ac_err2)
        
        serv.add_dep(serv_a)
        serv_a.add_dep(serv_b)
        serv_a.add_dep(serv_c)
        
        serv.prepare("start")
        serv.resume()
        
        self.assertEqual(serv.status, ERROR)
        self.assertEqual(serv_a.status, ERROR)
        self.assertEqual(serv_b.status, TOO_MANY_ERRORS)
        self.assertEqual(serv_c.status, TOO_MANY_ERRORS)
         
    def test_prepare_with_multiple_require_errors(self):
        """Test multiple require dependencies errors at different levels."""
        serv_base_error = Service("STAR_TREK")
        serv_ok_warnings = Service("KURK")
        serv_error = Service("SPOCK")
        serv_timed_out = Service("ENTREPRISE")
        
        ac_suc = Action(name="start", target="localhost", command="/bin/true")
        ac_tim = Action(name="start", target="localhost",
                     command="sleep 3", timeout=2)
        
        serv_base_error.add_action(ac_suc)
        serv_ok_warnings.add_action(ac_suc)
        serv_error.add_action(ac_suc)
        serv_timed_out.add_action(ac_tim)
        
        serv_base_error.add_dep(serv_ok_warnings)
        serv_base_error.add_dep(serv_error)
        serv_ok_warnings.add_dep(serv_timed_out, REQUIRE_WEAK)
        serv_error.add_dep(serv_timed_out)
        
        serv_base_error.prepare("start")
        serv_base_error.resume()
        
        self.assertEqual(serv_base_error.status, ERROR)
        self.assertEqual(serv_ok_warnings.status, RUNNING_WITH_WARNINGS)
        self.assertEqual(serv_error.status, ERROR)
        self.assertEqual(serv_timed_out.status, TIMED_OUT)
        
    def test_prepare_multiple_errors(self):
        """Test prepare with check and require deps with errors."""
        serv_a = Service("BASE")
        serv_b = Service("DEP_B")
        serv_c = Service("DEP_C")
        serv_d = Service("DEP_D")
        serv_x = Service("DEP_VX")
        serv_k = Service("DEP_K")
        
        act_suc = Action(name="start", target="localhost", command="/bin/true")
        act_status_failed = Action(name="status", target="localhost",
            command="/bin/false")
        act_status = Action(name="status", target="localhost",
                            command="/bin/true")
        
        serv_a.add_action(act_suc)
        serv_b.add_action(act_suc)
        serv_c.add_action(act_suc)
        serv_d.add_action(act_suc)
        serv_d.add_action(act_status)
        serv_x.add_action(act_suc)
        serv_k.add_action(act_status_failed)
        
        serv_a.add_dep(serv_x)
        serv_a.add_dep(serv_b)
        serv_a.add_dep(serv_c, REQUIRE_WEAK)
        
        serv_b.add_dep(serv_d, CHECK)
        
        serv_c.add_dep(serv_d)
        serv_c.add_dep(serv_k, CHECK)
        
        serv_a.prepare("start")
        serv_a.resume()
       
        self.assertEqual(serv_d.status, RUNNING)
        self.assertEqual(serv_k.status, TOO_MANY_ERRORS)
        self.assertEqual(serv_c.status, ERROR)
        self.assertEqual(serv_b.status, RUNNING)
        self.assertEqual(serv_x.status, RUNNING)
        self.assertEqual(serv_a.status, RUNNING_WITH_WARNINGS)
        
    def test_prepare_delayed_action(self):
        """Test prepare Service with a delayed action"""
        serv = Service("DELAYED_SERVICE")
        act_suc = ac_suc = Action(name="start",
                    target="localhost", command="/bin/true", delay=5)
        serv.add_action(act_suc)
        serv.prepare("start")
        serv.resume()
        self.assertEqual(serv.status, RUNNING)
        print "done in %ss" % serv.last_action().duration
        #self.assertTrue(serv.last_action().delayed)
        
    def test_prepare_multiple_delay(self):
        """Test prepare with dependencies and multiple delay"""
        serv = Service("BASE_DELAYED")
        serv_a = Service("A_NOT_DELAYED")
        serv_b = Service("B_DELAYED")
        serv_c = Service("C_DELAYED")
        act_a = ac_suc = Action(name="start",
                    target="localhost", command="/bin/true")
        act_serv = ac_suc = Action(name="start",
                    target="localhost", command="/bin/true", delay=1)
        act_b = ac_suc = Action(name="start",
                    target="localhost", command="/bin/true", delay=1)
        act_c = ac_suc = Action(name="start",
                    target="localhost", command="/bin/true", delay=2)
        serv.add_action(act_serv)
        serv_a.add_action(act_a)
        serv_b.add_action(act_b)
        serv_c.add_action(act_c)
        serv.add_dep(serv_a)
        serv.add_dep(serv_b)
        serv_a.add_dep(serv_c)
        serv_b.add_dep(serv_c)
        serv.prepare("start")
        serv.resume()
        self.assertEqual(serv.status, RUNNING)
        #self.assertTrue(serv.last_action().delayed)
        self.assertEqual(serv_a.status, RUNNING)
        #self.assertFalse(serv_a.last_action().delayed)
        self.assertEqual(serv_b.status, RUNNING)
        #self.assertTrue(serv_b.last_action().delayed)
        self.assertEqual(serv_c.status, RUNNING)
        #self.assertTrue(serv_c.last_action().delayed)
        
    def test_prepare_with_action_retry(self):
        """Test prepare with services that try to be retried."""
        serv = Service("BASE")
        serv_a = Service("NORMAL")
        serv_b = Service("RETRIED")
        suc = Action("start", "localhost", "/bin/true")
        ret = Action("start", "localhost", "/bin/false", delay=2)
        ret.retry = 4
        serv.add_action(suc)
        serv_a.add_action(suc)
        serv_b.add_action(ret)
        serv.add_dep(serv_a)
        serv.add_dep(serv_b)
        serv.prepare("start")
        serv.resume()
        
    def test_run_partial_deps(self):
        """Test stop algorithm as soon as the calling point is done."""
        serv = Service("NOT_CALLED")
        serv_a = Service("CALLING_POINT")
        serv_b = Service("SERV_1")
        serv_c = Service("SERV_2")
        act_suc = Action("start", "localhost", "/bin/true")
        serv_a.add_action(act_suc)
        serv_b.add_action(act_suc)
        serv_c.add_action(act_suc)
        serv.add_dep(serv_a)
        serv_a.add_dep(serv_b)
        serv_a.add_dep(serv_c)
        serv_a.run("start")
        self.assertEqual(serv.status, NO_STATUS)
        self.assertEqual(serv_a.status, RUNNING)
        self.assertEqual(serv_b.status, RUNNING)
        self.assertEqual(serv_c.status, RUNNING)
        
    def test_run_action_with_subaction(self):
        """Test with an action running a sub action (start-> status)"""
        serv = Service("BASE")
        act_start = Action("start", "localhost", "/bin/true")
        act_status = Action("status", "localhost", "/bin/true")
        act_status_fail = Action("status", "localhost", "/bin/false")
        act_start.add_dep(target=act_status, parent=False)
        serv.add_actions(act_start, act_status)
        serv.run("start")
        self.assertFalse(serv.last_action().worker)
        
        serv = Service("BASE")
        act_start.remove_dep(act_status.name)
        act_start.add_dep(target=act_status_fail, parent=False)
        serv.add_actions(act_start, act_status_fail)
        serv.run("start")
        self.assertTrue(serv.last_action().worker)
        
    def test_run_multiple_action_with_subaction(self):
        """Test with multiple actions running a sub action (start-> status)"""
        nemesis = Service("NEMESIS")
        zombie_one = Service("ZOMBIE_ONE")
        zombie_two = Service("ZOMBIE_TWO")
        hive = Service("THE_HIVE")
        
        act_suc = Action("start", "localhost", "/bin/true")
        act_sta = Action("status", "localhost", "/bin/true")
        act_sta_fai = Action("status", "localhost", "/bin/false")
      
        nemesis.add_action(act_suc)
        zombie_one.add_actions(act_suc, act_sta_fai)
        zombie_two.add_action(act_suc)
        hive.add_actions(act_suc, act_sta)
        
        zombie_one.add_dep(hive)
        zombie_two.add_dep(hive)
        nemesis.add_dep(zombie_one)
        nemesis.add_dep(zombie_two)
        
        nemesis.run("start")
        self.assertTrue(zombie_one.last_action().worker)