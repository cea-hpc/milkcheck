# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This modules defines the tests cases targeting the BaseService
"""
from unittest import TestCase

# Classes
from MilkCheck.Engine.BaseService import BaseService

# Symbols
from MilkCheck.Engine.Dependency import CHECK
from MilkCheck.Engine.BaseService import SUCCESS, IN_PROGRESS

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
        self.assertRaises(AssertionError,
            service.add_dependency, BaseService("dep3"), "hello")
    
    def test_remaining_dep_one(self):
        """Test the method remaining dependencies with one dependency."""
        service = BaseService("test_service")
        serv_a = BaseService("A")
        serv_b = BaseService("B")
        serv_a.status = SUCCESS
        service.add_dependency(serv_a)
        service.add_dependency(serv_b, CHECK)
        deps = service.remaining_dependencies()
        self.assertEqual(len(deps), 1, "should have one dependencies")
        self.assertTrue(serv_b.name == deps[0].target.name, "B should be in")
        
    def test_remaining_dep_several(self):
        """Test the method remaining dependencies with several dependencies."""
        service = BaseService("test_service")
        serv_a = BaseService("A")
        serv_b = BaseService("B")
        service.add_dependency(serv_a)
        service.add_dependency(serv_b, CHECK)
        deps = service.remaining_dependencies()
        
        self.assertEqual(len(deps), 2, "should have two dependencies")
        self.assertTrue(serv_a.name == deps[0].target.name, "A should be in")
        self.assertTrue(serv_b.name == deps[1].target.name, "B should be in")

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
        pass
