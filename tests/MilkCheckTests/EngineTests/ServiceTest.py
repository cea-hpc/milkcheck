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
from MilkCheck.Engine.BaseService import SUCCESS, TIMED_OUT, ERROR
from MilkCheck.Engine.BaseService import TOO_MANY_ERRORS
from MilkCheck.Engine.BaseService import SUCCESS_WITH_WARNINGS
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
        
    def test_has_too_many_errors(self):
        """Test the method has_too_many_errors."""
        action = Action(name="start", target="aury[12,13,21]",
                    command="/bin/false")
        action.errors = 2
        service = Service("test_service")
        service.add_action(action)
        service.prepare("start")
        service.resume()
        self.assertTrue(action.has_too_many_errors())
        
        act_test = Action(name="test", target="fortoy5", command="/bin/true")
        service.add_action(act_test)
        service.prepare("test")
        service.resume()
        self.assertFalse(action.has_too_many_errors())
        
    def test_has_timed_out(self):
        """Test has_timed_ou_method."""
        pass
    
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
    
    def test_add_dependency(self):
        """
        Test that you are not allowed to add an internal dependency
        to a service
        """
        ser = Service("SERVICE")
        self.assertRaises(AssertionError,ser.add_dependency,
            Service("A"), CHECK, True)
      
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
        service.add_dependency(serv_a)
        service.add_dependency(serv_b)
        self.assertRaises(ActionNotFoundError,
            service.prepare)
            
        #Service with dependencies and multiple levels
        serv_b.add_action(Action("start"))
        serv_c = Service("C")
        serv_a.add_dependency(serv_c, CHECK)
        self.assertRaises(ActionNotFoundError,
            service.prepare)
            
    def test_prepare_single_service(self):
        """Test prepare without dependencies between services."""
        serv_test = Service("test_service")
        ac_start = Action(name="start", target="localhost", command="/bin/true")
        serv_test.add_action(ac_start)
        serv_test.prepare("start")
        serv_test.resume()
        self.assertEqual(serv_test.status, SUCCESS)
        
    def test_prepare_one_dependency(self):
        """Test prepare with one dependency."""
        # Define the main service
        serv_test = Service("test_service")
        ac_start = Action(name="start", target="localhost", command="/bin/true")
        serv_test.add_action(ac_start)
        
        # Define the single dependency of the main service
        serv_dep = Service("dependency")
        serv_dep.add_action(ac_start)
        serv_test.add_dependency(serv_dep)
        
        # Start preparing of the base service
        serv_test.prepare("start")
        serv_test.resume()
        self.assertEqual(serv_test.status, SUCCESS)
        self.assertEqual(serv_dep.status, SUCCESS)
        
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
        
        serv_test.add_dependency(serv_depa)
        serv_test.add_dependency(serv_depb)
    
        serv_test.prepare("start")
        serv_test.resume()
        self.assertEqual(serv_test.status, SUCCESS)
        self.assertEqual(serv_depa.status, SUCCESS)
        self.assertEqual(serv_depb.status, SUCCESS)
        
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
        chiva.add_dependency(arth)
        
        # Service Dyonisos is declared here
        dion = Service("dionysos")
        dion.desc = "Perform tree on directory specified"
        dion.add_action(ac_start)
        dion.add_dependency(arth)
        
        # Service Brutus is declared here
        brut = Service("brutus")
        brut.desc = "Wanna sleep all the time"
        brut.add_action(ac_start)
        
        brut.add_dependency(chiva)
        brut.add_dependency(dion)
        
        brut.prepare("start")
        brut.resume()
        self.assertEqual(arth.status, SUCCESS)
        self.assertEqual(chiva.status, SUCCESS)
        self.assertEqual(dion.status, SUCCESS)
        self.assertEqual(brut.status, SUCCESS)
        
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
        
        serv.add_dependency(serv_b)
        serv.add_dependency(serv_a, REQUIRE_WEAK)
        
        serv.prepare("start")
        serv.resume()
        
        self.assertEqual(serv.status, SUCCESS_WITH_WARNINGS)
        self.assertEqual(serv_a.status, TOO_MANY_ERRORS)
        self.assertEqual(serv_b.status, SUCCESS)
        
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
        
        serv.add_dependency(serv_b)
        serv.add_dependency(serv_a)
        
        serv.prepare("start")
        serv.resume()
        
        self.assertEqual(serv.status, ERROR)
        self.assertEqual(serv_a.status, TOO_MANY_ERRORS)
        self.assertEqual(serv_b.status, SUCCESS)
   
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
        
        serv.add_dependency(serv_a)
        serv_a.add_dependency(serv_b)
        serv_a.add_dependency(serv_c)
        
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
        
        serv_base_error.add_dependency(serv_ok_warnings)
        serv_base_error.add_dependency(serv_error)
        serv_ok_warnings.add_dependency(serv_timed_out, REQUIRE_WEAK)
        serv_error.add_dependency(serv_timed_out)
        
        serv_base_error.prepare("start")
        serv_base_error.resume()
        
        self.assertEqual(serv_base_error.status, ERROR)
        self.assertEqual(serv_ok_warnings.status, SUCCESS_WITH_WARNINGS)
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
        
        action_a = Action("start")
        action_b = Action("start")
        action_c = Action("start")
        action_d_start = Action("start")
        action_d_status = Action("status")
        action_x = Action("start")
        action_k = Action("status")
        
        action_a.target = "aury1"
        action_b.target = "aury12"
        action_c.target = "aury[21,13]"
        action_d_start.target = "fortoy5"
        action_d_status.target = "fortoy[32,33]"
        action_x.target = "fortoy40"
        action_k.target = "aury12"
        
        action_a.command = "hostname"
        action_b.command = "echo hello world"
        action_c.command = "ls -l"
        action_d_start.command = "ps"
        action_d_status.command = "echo goodstatus"
        action_x.command = "sleep 2"
        action_k.command = "bad command"
        
        serv_a.add_action(action_a)
        serv_b.add_action(action_b)
        serv_c.add_action(action_c)
        serv_d.add_action(action_d_start)
        serv_d.add_action(action_d_status)
        serv_x.add_action(action_x)
        serv_k.add_action(action_k)
        
        serv_a.add_dependency(serv_x)
        serv_a.add_dependency(serv_b)
        serv_a.add_dependency(serv_c, REQUIRE_WEAK)
        
        serv_b.add_dependency(serv_d, CHECK)
        
        serv_c.add_dependency(serv_d)
        serv_c.add_dependency(serv_k, CHECK)
        
        serv_a.prepare("start")
        serv_a.resume()
       
        self.assertEqual(serv_d.status, SUCCESS)
        self.assertEqual(serv_k.status, TOO_MANY_ERRORS)
        self.assertEqual(serv_c.status, ERROR)
        self.assertEqual(serv_b.status, SUCCESS)
        self.assertEqual(serv_x.status, SUCCESS)
        self.assertEqual(serv_a.status, SUCCESS_WITH_WARNINGS)