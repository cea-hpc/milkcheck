# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This modules defines the tests cases targeting the BaseService
"""
import sys
from unittest import TestCase

# Classes
from MilkCheck.Engine.BaseService import BaseService
from MilkCheck.Engine.BaseService import IN_PROGRESS, SUCCESS, NO_STATUS

# Exceptions
from MilkCheck.Engine.BaseService import IllegalDependencyIdentifierError

class BaseServiceTest(TestCase):
    """
    Test cases for the class BaseService
    """
    def test_is_require_dep(self):
       """
       Test the mehtod is_require_dep
       """
       service = BaseService("test_service")
       serv_a = BaseService("A")
       serv_b = BaseService("B")
       service.add_dependency(serv_a)
       service.add_dependency(serv_b,"check")
       self.assertTrue(service.is_require_dep(serv_a))
       self.assertFalse(service.is_require_dep(serv_b))
                
    def test_is_check_dep(self):
       """
       Test method is check dep
       """
       service = BaseService("test_service")
       serv_a = BaseService("A")
       serv_b = BaseService("B")
       service.add_dependency(serv_a)
       service.add_dependency(serv_b,"check")
       self.assertFalse(service.is_check_dep(serv_a))
       self.assertTrue(service.is_check_dep(serv_b))
       
    def test_add_dependency(self):
        """
        Test the method add dependency
        """
        # Require dependency
        service = BaseService("test_service")
        rdep = BaseService("dep1")
        service.add_dependency(rdep)
        self.assertTrue(service.is_require_dep(rdep))
        
        # Check dependency
        cdep = BaseService("dep2")
        service.add_dependency(cdep,"check")
        self.assertTrue(service.is_check_dep(cdep))
                
        # Dependency with a None Service
        self.assertRaises(TypeError,service.add_dependency, None)
            
        # Dependency with bad name identifier
        self.assertRaises(IllegalDependencyIdentifierError,
            service.add_dependency, BaseService("dep3"), "hello")
        
    def test_remaining_dependencies(self):
        """
        Test the method remaining dependencies
        """
        service = BaseService("test_service")
        serv_a = BaseService("A")
        serv_b = BaseService("B")
        service.add_dependency(serv_a)
        service.add_dependency(serv_b,"check")
        deps = service._remaining_dependencies()
        
        self.assertEqual(len(deps), 2, "should have two dependencies")
        self.assertEqual(serv_a.name, deps[0][0].name, "A should be in")
        self.assertEqual(serv_b.name, deps[1][0].name, "B should be in")
        
        service.cleanup_dependencies()
        
        serv_a.status = IN_PROGRESS
        service.add_dependency(serv_a)
        service.add_dependency(serv_b,"check")
        deps = service._remaining_dependencies()
        self.assert_(len(deps) == 1, "should have one dependencies")
        self.assert_(serv_b.name == deps[0][0].name, "B should be in")

    def test_update_status(self):
        """
        Test the method update_status
        """
        #Test status updated
        service = BaseService("test_service")
        service.update_status(IN_PROGRESS)
        self.assert_(service.status == IN_PROGRESS)
        service.status = NO_STATUS
        
        """
        There is a dependency between test_service and A. As soon as
        test_service does a prepare() A status must be modified to
        IN_PROGRESS
        """
        serv_a = BaseService("A")
        service.add_dependency(serv_a)
#        service.prepare()
#        self._assert(serv_a.status == IN_PROGRESS, "A must be IN_PROGRESS")
