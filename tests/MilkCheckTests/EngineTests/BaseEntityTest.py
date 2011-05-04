# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
Test cases for the BaseEntity classes.
"""

import unittest

# Classes
from MilkCheck.Engine.BaseEntity import BaseEntity
from MilkCheck.Engine.Dependency import Dependency

# Symbols
from MilkCheck.Engine.Dependency import CHECK, REQUIRE, REQUIRE_WEAK
from MilkCheck.Engine.BaseEntity import NO_STATUS, DONE, WAITING_STATUS
from MilkCheck.Engine.BaseEntity import TIMED_OUT, ERROR, TOO_MANY_ERRORS
from MilkCheck.Engine.BaseEntity import DONE_WITH_WARNINGS

# Exceptions
from MilkCheck.Engine.BaseEntity import IllegalDependencyTypeError
from MilkCheck.Engine.BaseEntity import DependencyAlreadyReferenced

class BaseEntityTest(unittest.TestCase):
    """Tests cases for the class BaseEntity."""
    
    def test_instanciation_base_entity(self):
        """Test BaseEntity object instanciation."""
        ent = BaseEntity('foo')
        self.assertTrue(ent)
        self.assertTrue(isinstance(ent, BaseEntity))
        self.assertEqual(ent.name, 'foo')
        ent = BaseEntity(name='foo', target='fortoy5')
        self.assertEqual(ent.target, 'fortoy5')

    def test_add_dep_parents(self):
        """Test method add dependency for parents"""
        ent = BaseEntity('foo')
        ent_dep = BaseEntity('parent')
        ent.add_dep(ent_dep)
        self.assertTrue(ent.has_parent_dep('parent'))
        self.assertTrue(ent_dep.has_child_dep('foo'))
        
    def test_add_dep_children(self):
        """Test method add_dep for children"""
        ent = BaseEntity('foo')
        ent_dep = BaseEntity('child')
        ent.add_dep(target=ent_dep, parent=False)
        self.assertTrue(ent.has_child_dep('child'))
        self.assertTrue(ent_dep.has_parent_dep('foo'))
        
    def test_add_dep_bad_cases(self):
        """Test bad usage of the method add_dep"""
        ent = BaseEntity('foo')
        ent_dep = BaseEntity('child')
        ent.add_dep(ent_dep, CHECK)
                
        # Dependency with a None Service
        self.assertRaises(AssertionError, ent.add_dep, None)
            
        # Dependency with bad name identifier
        self.assertRaises(IllegalDependencyTypeError,
            ent.add_dep, BaseEntity('A'), 'BAD')
            
        #Already referenced dependency 
        r_ent = BaseEntity('child')
        self.assertRaises(DependencyAlreadyReferenced,
            ent.add_dep, r_ent)
        
    def test_remove_dep(self):
        """Test method remove_dep."""
        ent = BaseEntity('foo')
        ent_dep = BaseEntity('child')
        ent.children['child'] = Dependency(ent_dep)
        ent_dep.parents['foo'] = Dependency(ent)
        ent.remove_dep('child', parent=False)
        self.assertTrue('child' not in ent.children)
        self.assertTrue('foo' not in ent.parents)
        self.assertRaises(AssertionError, ent.remove_dep, None)
        
    def test_has_child_dep(self):
        """Test method has_child_dep"""
        ent = BaseEntity('foo')
        ent_dep = BaseEntity('child')
        ent.children['child'] = Dependency(ent_dep)
        self.assertTrue(ent.has_child_dep('child'))
        del ent.children['child']
        self.assertFalse(ent.has_child_dep('child'))
        
    def test_has_parent_dep(self):
        """Test method has_parent_dep"""
        ent = BaseEntity('foo')
        ent_dep = BaseEntity('parent')
        ent.parents['parent'] = Dependency(ent_dep)
        self.assertTrue(ent.has_parent_dep('parent'))
        del ent.parents['parent']
        self.assertFalse(ent.has_parent_dep('parent'))
        
    def test_is_ready(self):
        """Test method allowing us to determine if a service can be processed"""
        ent = BaseEntity('foo')
        ent_dep = BaseEntity('parent')
        ent_dep2 = BaseEntity('parent2')
        ent.add_dep(ent_dep)
        ent.add_dep(ent_dep2)
        self.assertFalse(ent.is_ready())
        ent_dep.status = WAITING_STATUS
        self.assertFalse(ent.is_ready())
        ent_dep.status = DONE
        ent_dep2.status = DONE
        self.assertTrue(ent.is_ready())
        
    def test_clear_deps(self):
        """Test method clear_deps"""
        ent = BaseEntity('foo')
        ent_dep = BaseEntity('parent')
        ent.add_dep(ent_dep)
        self.assertEqual(len(ent.parents), 1)
        ent.clear_deps()
        self.assertEqual(len(ent.parents), 0)
       
    def test_search_deps(self):
        """Test method search_deps"""
        ent = BaseEntity('test_service')
        ent_a = BaseEntity('A')
        ent_b = BaseEntity('B')
        ent.add_dep(ent_a)
        ent.add_dep(ent_b, CHECK)
        self.assertEqual(len(ent.search_deps()), 2)
        self.assertEqual(len(ent.search_deps([NO_STATUS])), 2)
        ent_c = BaseEntity('C')
        ent_c.status = DONE
        ent.add_dep(ent_c)
        self.assertEqual(len(ent.search_deps([NO_STATUS])), 2)
        self.assertEqual(len(ent.search_deps([NO_STATUS, DONE])), 3)

    def test_eval_deps_no_status(self):
        """Test that eval_deps_status return NO_STATUS"""
        service = BaseEntity("test_service")
        serv_a = BaseEntity("A")
        serv_b = BaseEntity("B")
        serv_a.status = DONE_WITH_WARNINGS
        service.add_dep(serv_a)
        service.add_dep(serv_b, CHECK)
        self.assertEqual(service.eval_deps_status(), NO_STATUS)

    def test_eval_deps_waiting(self):
        """Test that eval_deps_status return WAITING_STATUS"""
        service = BaseEntity("test_service")
        serv_a = BaseEntity("A")
        serv_b = BaseEntity("B")
        service.add_dep(serv_a)
        service.add_dep(serv_b, CHECK)
        serv_a.status = WAITING_STATUS
        self.assertEqual(service.eval_deps_status(), WAITING_STATUS)

    def test_eval_deps_error(self):
        """Test that eval_deps_status return ERROR"""
        service = BaseEntity("test_service")
        serv_a = BaseEntity("A")
        serv_b = BaseEntity("B")
        service.add_dep(serv_a)
        service.add_dep(serv_b, CHECK)
        serv_b.status = DONE
        serv_a.status = TIMED_OUT
        self.assertEqual(service.eval_deps_status(), ERROR)

    def test_eval_deps_warnings(self):
        """Test that eval_deps_status return DONE_WITH_WARNINGS"""
        service = BaseEntity("test_service")
        serv_a = BaseEntity("A")
        serv_b = BaseEntity("B")
        service.add_dep(serv_a, REQUIRE_WEAK)
        service.add_dep(serv_b, REQUIRE_WEAK)
        serv_b.status = TOO_MANY_ERRORS
        serv_a.status = TIMED_OUT
        self.assertEqual(service.eval_deps_status(), DONE_WITH_WARNINGS)