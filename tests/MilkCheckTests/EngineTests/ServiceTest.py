# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This modules defines the tests cases targeting the Action and Service objects
"""

import sys
from unittest import TestCase

# Classes
from MilkCheck.Engine.Service import Service
from MilkCheck.Engine.Action import Action

# Exceptions
from MilkCheck.Engine.Service import ActionAlreadyReferencedError
from MilkCheck.Engine.Service import ActionNotFoundError

# Symbols
from MilkCheck.Engine.BaseService import SUCCESS

class ActionTest(TestCase):
    """
    Define the unit tests for the object action
    """
    def test_action_instanciation(self):
        """Test instanciation of an action"""
        action = Action("start")
        self.assertNotEqual(action, None, "should be none")
        self.assertEqual(action.name, "start", "wrong name")
        
    def test_has_too_many_errors(self):
        """
        Test the method has_too_many_errors
        """
        action = Action("start")
        action.errors = 2
        action.command = "hostnam"
        action.target = "aury[13,14,21]"
        service = Service("test_service")
        service.add_action(action)
        service.prepare("start")
        service.resume()
        self.assertTrue(action.has_too_many_errors())
        
        act_test = Action("test")
        action.command = "hostnam"
        action.target = "aury[13,14,21]"
        service.add_action(act_test)
        service.prepare("test")
        service.resume()
        self.assertFalse(action.has_too_many_errors())
        
    def test_has_timed_out(self):
        """
        Test has_timed_ou_method
        """
        pass
    
class ServiceTest(TestCase):
    """
    Define the unit tests for the object service
    """
    def test_service_instanciation(self):
        """
        Test instanciation of a service
        """
        service = Service("brutus")
        self.assertNotEqual(service, None, "should be none")
        self.assertEqual(service.name, "brutus", "wrong name")
        
    def test_add_action(self):
        """
        Test add_action's behaviour
        """
        service = Service("brutus")
        service.add_action(Action("start"))
        self.assertTrue(service.has_action("start"))
        self.assertRaises(ActionAlreadyReferencedError,
                service.add_action,Action("start"))
                
    def test_remove_action(self):
        """
        Test remove_action behaviour
        """
        service = Service("brutus")
        service.add_action(Action("start"))
        service.remove_action("start")
        self.assertFalse(service.has_action("start"))
        self.assertRaises(ActionNotFoundError,
            service.remove_action, "start")
    
    def test_last_action(self):
        """
        Test last_action method behaviour
        """
        service = Service("henry")
        self.assertRaises(ActionNotFoundError, service.last_action)
        
        start = Action("start")
        start.target = "aury12"
        start.command = "hostname"
        service.add_action(start)
        self.assertRaises(ActionNotFoundError, service.last_action)
        
        service.prepare("start")
        self.assertTrue(service.last_action())
        
    def test_prepare_error(self):
        
        """
        Test prepare exception if action is not found
        """
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
        serv_a.add_dependency(serv_c,"check")
        self.assertRaises(ActionNotFoundError,
            service.prepare)
            
    def test_prepare_single_service(self):
        """
        Test prepare without dependencies between services
        """
        serv_test = Service("test_service")
        act_start = Action("start")
        act_start.target="aury[11-12]"
        act_start.command = "echo HelloWorld"
        serv_test.add_action(act_start)
        serv_test.prepare("start")
        serv_test.resume()
        self.assertEqual(serv_test.status, SUCCESS)
        
    def test_prepare_service_with_one_dependency(self):
        """
        Test prepare with one dependency
        """
        # Define the main service
        serv_test = Service("test_service")
        act_start = Action("start")
        act_start.target="aury[11-12]"
        act_start.command = "echo HelloWorld from serv_test"
        serv_test.add_action(act_start)
        
        # Define the single dependency of the main service
        serv_dep = Service("dependency")
        act_start = Action("start")
        act_start.target="aury21"
        act_start.command = "echo HelloWorld from serv_dep"
        serv_dep.add_action(act_start)
        serv_test.add_dependency(serv_dep)
        
        # Start preparing of the base service
        serv_test.prepare("start")
        serv_test.resume()
        self.assertEqual(serv_test.status, SUCCESS)
        self.assertEqual(serv_dep.status, SUCCESS)
        
    def test_prepare_sevice_with_several_dependency(self):
        """
        Test prepare with several dependencies at the same level
        """
        # Define the main service
        serv_test = Service("test_service")
        act_start = Action("start")
        act_start.target="aury[11-12]"
        act_start.command = "echo HelloWorld from serv_test"
        serv_test.add_action(act_start)
        
        # Define the dependency DEP_A 
        serv_depa = Service("DEP_A")
        act_start = Action("start")
        act_start.target="fortoy[5-6]"
        act_start.command = "echo HelloWorld from DEP_A"
        serv_depa.add_action(act_start)
        
        # Define the dependency DEP_B
        serv_depb = Service("DEP_B")
        act_start = Action("start")
        act_start.target="aury21"
        act_start.command = "sleep 3"
        serv_depb.add_action(act_start)
        
        serv_test.add_dependency(serv_depa)
        serv_test.add_dependency(serv_depb)
    
        serv_test.prepare("start")
        serv_test.resume()
        self.assertEqual(serv_test.status, SUCCESS)
        self.assertEqual(serv_depa.status, SUCCESS)
        self.assertEqual(serv_depb.status, SUCCESS)
        
    def test_prepare_service_with_multiple_multilevel_dependencies(self):
        """
        Test prepare with multiple dependencies at different levels
        """
        #Service Arthemis is delcared here
        arth = Service("arthemis")
        arth.desc = "Sleep five seconds"
        arth_start = Action("start")
        arth_start.command = "sleep 5"
        arth_start.target = "aury21"
        arth.add_action(arth_start)
        
        # Service Chiva is declared here
        chiva = Service("chiva")
        chiva.desc = "List all processes in details"
        chiva_start = Action("start")
        chiva_start.target = "aury[11-12]"
        chiva_start.command = "ps -el"
        chiva.add_action(chiva_start)
        chiva.add_dependency(arth)
        
        # Service Dyonisos is declared here
        dion = Service("dionysos")
        dion.desc = "Perform tree on directory specified"
        dion_start = Action("start")
        dion_start.target = "aury13"
        dion_start.command = "tree /sbin/service"
        dion.add_action(dion_start)
        dion.add_dependency(arth)
        
        # Service Brutus is declared here
        brut = Service("brutus")
        brut.desc = "Wanna sleep all the time"
        brut_start = Action("start")
        brut_start.target = "aury[21,12,26]"
        brut_start.command = "sleep 2"
        brut.add_action(brut_start)
        
        brut.add_dependency(chiva)
        brut.add_dependency(dion)
        
        brut.prepare("start")
        brut.resume()
        self.assertEqual(arth.status, SUCCESS)
        self.assertEqual(chiva.status, SUCCESS)
        self.assertEqual(dion.status, SUCCESS)
        self.assertEqual(brut.status, SUCCESS)