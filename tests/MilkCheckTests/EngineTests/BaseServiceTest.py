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
from MilkCheck.Engine.BaseService import NO_STATUS, SUCCESS, IN_PROGRESS
from MilkCheck.Engine.BaseService import TIMED_OUT, TOO_MANY_ERRORS
from MilkCheck.Engine.BaseService import SUCCESS_WITH_WARNINGS, ERROR

# Exceptions
from MilkCheck.Engine.Dependency import IllegalDependencyTypeError
from MilkCheck.Engine.BaseService import DependencyAlreadyReferenced 


class BaseServiceTest(TestCase):
    """
    Test cases for the class BaseService
    """
    def test_add_dependency(self):
        """Test the method add dependency."""
        # Require dependency
        service = BaseService("test_service")
        rdep = BaseService("dep1")
        service.add_dependency(rdep)
        self.assertTrue(service.has_dependency(rdep.name))
        
        # Check dependency
        cdep = BaseService("dep2")
        service.add_dependency(cdep, CHECK)
        self.assertTrue(service.has_dependency(cdep.name))
                
        # Dependency with a None Service
        self.assertRaises(TypeError, service.add_dependency, None)
            
        # Dependency with bad name identifier
        self.assertRaises(IllegalDependencyTypeError,
            service.add_dependency, BaseService("A"), "BAD")
        #Already referenced dependency 
        self.assertRaises(DependencyAlreadyReferenced,
            service.add_dependency, rdep)
       
    def test_has_dep_in_progress(self):
        """Test the method has_dep_in_progress."""
        service = BaseService("test_service")
        serv_a = BaseService("A")
        service.add_dependency(serv_a)
        self.assertFalse(service.has_in_progress_dep())
        serv_b = BaseService("B")
        serv_b.status = IN_PROGRESS
        service.add_dependency(serv_b)
        self.assertTrue(service.has_in_progress_dep())
        
    def test_update_status(self):
        """Test the method update_status without children."""
        #Test status updated
        service = BaseService("test_service")
        service.update_status(IN_PROGRESS)
        self.assertEqual(service.status, IN_PROGRESS)
        
        service.update_status(SUCCESS)
        self.assertEqual(service.status,  SUCCESS)
        
    def test_update_status_children(self):
        """Test the method update_status with children."""
        serv_a = BaseService("HIGHER_POINT")
        serv_b = BaseService("LEFT_POINT")
        serv_c = BaseService("RIGHT_POINT")
        serv_b.add_dependency(serv_a)
        serv_c.add_dependency(serv_a)
        self.assertRaises(NotImplementedError, serv_a.update_status, SUCCESS)
        
    def test_run(self):
        """Test the method run"""
        serv_a = BaseService("HIGHER_POINT")
        self.assertRaises(NotImplementedError, serv_a.run, 'fake')
        self.assertTrue(serv_a.origin)
        
    def test_search_deps(self):
        """Test the method search dep."""
        service = BaseService("test_service")
        serv_a = BaseService("A")
        serv_b = BaseService("B")
        service.add_dependency(serv_a)
        service.add_dependency(serv_b, CHECK)
        self.assertEqual(len(service.search_deps()), 2)
        self.assertEqual(len(service.search_deps([NO_STATUS])), 2)
        serv_c = BaseService("C")
        serv_c.status = SUCCESS
        service.add_dependency(serv_c)
        self.assertEqual(len(service.search_deps([NO_STATUS])), 2)
        self.assertEqual(len(service.search_deps([NO_STATUS, SUCCESS])), 3)
        
    def test_eval_deps_no_status(self):
        """Test that eval_deps_status return NO_STATUS"""
        service = BaseService("test_service")
        serv_a = BaseService("A")
        serv_b = BaseService("B")
        serv_a.status = SUCCESS_WITH_WARNINGS
        service.add_dependency(serv_a)
        service.add_dependency(serv_b, CHECK)
        self.assertEqual(service.eval_deps_status(), NO_STATUS)
    
    def test_eval_deps_in_progress(self):
        """Test that eval_deps_status return IN_PROGRESS"""
        service = BaseService("test_service")
        serv_a = BaseService("A")
        serv_b = BaseService("B")
        service.add_dependency(serv_a)
        service.add_dependency(serv_b, CHECK)
        serv_a.status = IN_PROGRESS
        self.assertEqual(service.eval_deps_status(), IN_PROGRESS)
        
    def test_eval_deps_error(self):
        """Test that eval_deps_status return ERROR"""
        service = BaseService("test_service")
        serv_a = BaseService("A")
        serv_b = BaseService("B")
        service.add_dependency(serv_a)
        service.add_dependency(serv_b, CHECK)
        serv_b.status = SUCCESS
        serv_a.status = TIMED_OUT
        self.assertEqual(service.eval_deps_status(), ERROR)
      
    def test_eval_deps_warnings(self):
        """Test that eval_deps_status return SUCCESS_WITH_WARNINGS"""
        service = BaseService("test_service")
        serv_a = BaseService("A")
        serv_b = BaseService("B")
        service.add_dependency(serv_a, REQUIRE_WEAK)
        service.add_dependency(serv_b, REQUIRE_WEAK)
        serv_b.status = TOO_MANY_ERRORS
        serv_a.status = TIMED_OUT
        self.assertEqual(service.eval_deps_status(), SUCCESS_WITH_WARNINGS)