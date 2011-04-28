# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This modules defines the tests cases targeting the BaseService
"""
from unittest import TestCase

# Classes
from MilkCheck.Engine.BaseService import BaseService

# Symbols
from MilkCheck.Engine.Dependency import CHECK, REQUIRE_WEAK
from MilkCheck.Engine.BaseService import NO_STATUS, RUNNING, WAITING_STATUS
from MilkCheck.Engine.BaseService import TIMED_OUT, TOO_MANY_ERRORS
from MilkCheck.Engine.BaseService import RUNNING_WITH_WARNINGS, ERROR

class BaseServiceTest(TestCase):
    """
    Test cases for the class BaseService
    """
        
    def test_update_status(self):
        """Test the method update_status without children."""
        #Test status updated
        service = BaseService("test_service")
        service.update_status(WAITING_STATUS)
        self.assertEqual(service.status, WAITING_STATUS)
        
        service.update_status(RUNNING)
        self.assertEqual(service.status,  RUNNING)
        
    def test_update_status_children(self):
        """Test the method update_status with children."""
        serv_a = BaseService("HIGHER_POINT")
        serv_b = BaseService("LEFT_POINT")
        serv_c = BaseService("RIGHT_POINT")
        serv_b.add_dep(serv_a)
        serv_c.add_dep(serv_a)
        self.assertRaises(NotImplementedError, serv_a.update_status, RUNNING)
        
    def test_run(self):
        """Test the method run"""
        serv_a = BaseService("HIGHER_POINT")
        self.assertRaises(NotImplementedError, serv_a.run, 'fake')
        self.assertTrue(serv_a.origin)
        
    def test_eval_deps_no_status(self):
        """Test that eval_deps_status return NO_STATUS"""
        service = BaseService("test_service")
        serv_a = BaseService("A")
        serv_b = BaseService("B")
        serv_a.status = RUNNING_WITH_WARNINGS
        service.add_dep(serv_a)
        service.add_dep(serv_b, CHECK)
        self.assertEqual(service.eval_deps_status(), NO_STATUS)
    
    def test_eval_deps_waiting(self):
        """Test that eval_deps_status return WAITING_STATUS"""
        service = BaseService("test_service")
        serv_a = BaseService("A")
        serv_b = BaseService("B")
        service.add_dep(serv_a)
        service.add_dep(serv_b, CHECK)
        serv_a.status = WAITING_STATUS
        self.assertEqual(service.eval_deps_status(), WAITING_STATUS)
        
    def test_eval_deps_error(self):
        """Test that eval_deps_status return ERROR"""
        service = BaseService("test_service")
        serv_a = BaseService("A")
        serv_b = BaseService("B")
        service.add_dep(serv_a)
        service.add_dep(serv_b, CHECK)
        serv_b.status = RUNNING
        serv_a.status = TIMED_OUT
        self.assertEqual(service.eval_deps_status(), ERROR)
      
    def test_eval_deps_warnings(self):
        """Test that eval_deps_status return RUNNING_WITH_WARNINGS"""
        service = BaseService("test_service")
        serv_a = BaseService("A")
        serv_b = BaseService("B")
        service.add_dep(serv_a, REQUIRE_WEAK)
        service.add_dep(serv_b, REQUIRE_WEAK)
        serv_b.status = TOO_MANY_ERRORS
        serv_a.status = TIMED_OUT
        self.assertEqual(service.eval_deps_status(), RUNNING_WITH_WARNINGS)