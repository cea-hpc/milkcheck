# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This module contains the DependencyTest class.
"""

# Classes
from unittest import TestCase
from MilkCheck.Engine.Dependency import Dependency 
from MilkCheck.Engine.Service import Service
from MilkCheck.Engine.ServiceGroup import ServiceGroup

# Exceptions
from MilkCheck.Engine.BaseEntity import IllegalDependencyTypeError

# Symbols
from MilkCheck.Engine.Dependency import CHECK, REQUIRE, REQUIRE_WEAK

class DependencyTest(TestCase):
    """Dependency test cases."""
    
    def test_dependency_instanciation(self):
        """Test instanciation of a dependency."""
        service = Service("PARENT")
        service = Service("CHILD")
        self.assertRaises(AssertionError, Dependency, None)
        self.assertRaises(AssertionError, Dependency, service, "TEST")
        self.assertTrue(Dependency(service))
        self.assertTrue(Dependency(service, CHECK))
        self.assertTrue(Dependency(service, CHECK, True))
    
    def test_is_weak_dependency(self):
        """Test the behaviour of the method is_weak."""
        dep_a = Dependency(Service("Base"), CHECK)
        dep_b = Dependency(Service("Base"), REQUIRE)
        dep_c = Dependency(Service("Base"), REQUIRE_WEAK)
        self.assertFalse(dep_a.is_weak())
        self.assertFalse(dep_b.is_weak())
        self.assertTrue(dep_c.is_weak())
        
    def test_is_strong_dependency(self):
        """Test the behaviour of is_strong method."""
        dep_a = Dependency(Service("Base"), CHECK)
        dep_b = Dependency(Service("Base"), REQUIRE)
        dep_c = Dependency(Service("Base"), REQUIRE_WEAK)
        self.assertTrue(dep_a.is_strong())
        self.assertTrue(dep_b.is_strong())
        self.assertFalse(dep_c.is_strong())

    def test_set_dep_type_property(self):
        """Test assignement to dependency type."""
        dep = Dependency(Service("Base"))
        self.assertRaises(AssertionError,
            dep.set_dep_type, "TEST")
        dep.dep_type = CHECK
        self.assertEqual(dep._dep_type, CHECK)
        
    def test_is_internal(self):
        """Test the behaviour of the method is internal"""
        dep = Dependency(target=ServiceGroup('Group'), intr=True)
        self.assertTrue(dep.is_internal())
        dep = Dependency(target=ServiceGroup('Group'), intr=False)
        self.assertFalse(dep.is_internal())