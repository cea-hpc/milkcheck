# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
Test cases for the BaseEntity classes.
"""

import unittest

# Classes
from ClusterShell.NodeSet import NodeSet, NodeSetException
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
from MilkCheck.Engine.BaseEntity import UndefinedVariableError
from MilkCheck.Engine.BaseEntity import InvalidVariableError

class BaseEntityTest(unittest.TestCase):
    """Tests cases for the class BaseEntity."""

    def test_instanciation_base_entity(self):
        """Test BaseEntity object instanciation."""
        ent = BaseEntity('foo')
        self.assertTrue(ent)
        self.assertTrue(isinstance(ent, BaseEntity))
        self.assertEqual(ent.name, 'foo')
        ent = BaseEntity(name='foo', target='fortoy5')
        self.assertTrue('fortoy5' in ent.target)
        ent = BaseEntity(name='foo', target=NodeSet('fortoy[8-15]'))
        self.assertTrue(NodeSet('fortoy[8-15]') == ent.target)
        self.assertRaises(NodeSetException, BaseEntity, name='foo',
                            target='[fortoy]')

    def test_update_target(self):
        '''Test update of the target of an entity'''
        ent = BaseEntity(name='foo', target='fortoy[5-10]')
        ent.update_target(NodeSet('fortoy[5-8]'))
        self.assertTrue(ent.target == NodeSet('fortoy[5-8]'))
        ent.update_target('fortoy[4-6]', mode='DIF')
        self.assertTrue(ent.target == NodeSet('fortoy[7-8]'))
        ent.update_target('fortoy8', mode='INT')
        self.assertTrue(ent.target == NodeSet('fortoy8'))

    def test_reset_entity(self):
        '''Test reset entity'''
        ent = BaseEntity(name='foo', target='fortoy5')
        ent.status = NO_STATUS
        ent.algo_reverse = True
        ent.reset()
        self.assertEqual(ent._algo_reversed, False)
        self.assertEqual(ent.status, NO_STATUS)

    def test_search_leafs(self):
        '''Test research of leafs within the graph'''
        ent1 = BaseEntity('ent1')
        ent2 = BaseEntity('ent2')
        ent3 = BaseEntity('ent3')
        ent4 = BaseEntity('ent4')
        self.assertTrue(ent1.search_leafs())
        self.assertTrue(len(ent1.search_leafs()), 1)
        ent1.add_dep(target=ent2)
        ent1.add_dep(target=ent3)
        ent2.add_dep(target=ent4)
        self.assertTrue(ent1.search_leafs())
        self.assertTrue(len(ent1.search_leafs()), 2)

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

    def test_search_node_graph(self):
        """Test the research of a node through a graph"""
        ent1 = BaseEntity('E1')
        ent2 = BaseEntity('E2')
        ent3 = BaseEntity('E3')
        ent4 = BaseEntity('E4')
        ent1.add_dep(ent2)
        ent1.add_dep(ent3)
        ent2.add_dep(ent4)
        ent3.add_dep(ent4)
        self.assertTrue(ent1.search('E3') is ent3)
        self.assertTrue(ent1.search('E5') is None)

    def test_search_node_graph_reverse(self):
        """Test the research of node through a graph in reverse mod"""
        ent1 = BaseEntity('E1')
        ent2 = BaseEntity('E2')
        ent3 = BaseEntity('E3')
        ent4 = BaseEntity('E4')
        ent1.add_dep(ent2)
        ent1.add_dep(ent3)
        ent2.add_dep(ent4)
        ent3.add_dep(ent4)
        self.assertTrue(ent4.search('E1', True) is ent1)
        self.assertTrue(ent4.search('E5', True) is None)

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
        serv_a.status = NO_STATUS
        serv_b.status = DONE_WITH_WARNINGS
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
        serv_a.status = DONE
        serv_b.status = DONE_WITH_WARNINGS
        self.assertEqual(service.eval_deps_status(), DONE_WITH_WARNINGS)

    def test_lookup_variables1(self):
        '''Test variables resolution through a single entity'''
        service = BaseEntity('test_service')
        service.add_var('VAR', 'test')
        symbols = {'VAR': None}
        service._lookup_variables(symbols)
        self.assertEqual(symbols['VAR'], 'test')

    def test_lookup_variables2(self):
        '''Test variables resolution through multiple entities'''
        service = BaseEntity('test_service')
        service.add_var('VAR', 'test')
        group = BaseEntity('group_service')
        group.add_var('GVAR', 'group')
        service.parent = group
        symbols = {'VAR': None, 'GVAR': None}
        service._lookup_variables(symbols)
        self.assertEqual(symbols['VAR'], 'test')
        self.assertEqual(symbols['GVAR'], 'group')

    def test_lookup_variables3(self):
        '''Test variables resolution with an undefined var'''
        service = BaseEntity('test_service')
        service.add_var('VAR', 'test')
        group = BaseEntity('group_service')
        group.add_var('GVAR', 'group')
        service.parent = group
        symbols = {'VAR': None, 'GVAR': None, 'BAD_VAR': None}
        self.assertRaises(UndefinedVariableError,
            service._lookup_variables, symbols)

    def test_lookup_variables4(self):
        '''Test variables resolution with a var referencing a property'''
        service = BaseEntity('test_service')
        service.add_var('VAR', 'test')
        group = BaseEntity('group_service')
        group.add_var('GVAR', 'group')
        service.parent = group
        symbols = {'VAR': None, 'GVAR': None, 'TARGET': None, 'NAME': None}
        service._lookup_variables(symbols)
        self.assertEqual(symbols['VAR'], 'test')
        self.assertEqual(symbols['GVAR'], 'group')
        self.assertEqual(symbols['TARGET'], NodeSet())
        self.assertEqual(symbols['NAME'], 'test_service')

    def test_resolve_property1(self):
        '''Test replacement of symbols within a property'''
        service = BaseEntity('test_service')
        service.add_var('NODES', 'localhost,127.0.0.1')
        service.desc = 'start %NAME on %TARGET'
        service.target = '%NODES'
        self.assertEqual(service.resolve_property('target'),
            NodeSet('localhost,127.0.0.1'))
        self.assertEqual(service.resolve_property('name'),
            'test_service')
        self.assertEqual(service.resolve_property('desc'),
            'start test_service on 127.0.0.1,localhost')

    def test_resolve_property2(self):
        '''Test with nothing to replace in the property'''
        service = BaseEntity('test_service')
        group = BaseEntity('group_service')
        service.parent = group
        self.assertEqual(service.resolve_property('parent'), group)

    def test_resolve_property3(self):
        '''Test resolution with a property containing a shell variable'''
        service = BaseEntity('test_service')
        service.target = '$(echo localhost,127.0.0.1)'
        self.assertEqual(service.resolve_property('target'),
            NodeSet('localhost,127.0.0.1'))

    def test_resolve_property4(self):
        '''
        Test resolution with a property containing an invalid shell variable
        '''
        service = BaseEntity('test_service')
        error = False
        try:
            service.target = '$(/bin/false)'
        except InvalidVariableError:
            error = True
        self.assertTrue(error)

    def test_resolve_property5(self):
        '''Test resolution with a property containing special characters'''
        service = BaseEntity('test_service')
        service.add_var('NODES', '@testgrp!@agrp,epsilon')
        service.target = '%NODES'
        self.assertEqual(service.resolve_property('target'),
            NodeSet('@testgrp!@agrp,epsilon'))

    def test_inheritance_of_properties1(self):
        '''Test inheritance between entities'''
        ent1 = BaseEntity(name='parent', target='aury[10-16]')
        ent1.fanout = 5
        ent1.errors = 2
        ent1.timeout = 15
        ent2 = BaseEntity(name='child')
        ent2.inherits_from(ent1)
        self.assertEqual(ent2.target, NodeSet('aury[10-16]'))
        self.assertEqual(ent2.fanout, 5)
        self.assertEqual(ent2.errors, 2)
        self.assertEqual(ent2.timeout, 15)

    def test_inheritance_of_properties2(self):
        '''
        Test inheritance between entities but some properties are
        not inherited
        '''
        ent1 = BaseEntity(name='parent', target='aury[10-16]')
        ent1.fanout = 5
        ent1.errors = 2
        ent2 = BaseEntity(name='child')
        ent2.fanout = 2
        ent2.errors = 3
        ent2.timeout = 15
        ent2.inherits_from(ent1)
        self.assertEqual(ent2.target, NodeSet('aury[10-16]'))
        self.assertEqual(ent2.fanout, 2)
        self.assertEqual(ent2.errors, 3)
        self.assertEqual(ent2.timeout, 15)

    def test_clear_parents(self):
        '''Test remove all parents dependencies'''
        ent1 = BaseEntity(name='A')
        ent2 = BaseEntity(name='B')
        ent3 = BaseEntity(name='C')
        ent1.add_dep(target=ent2)
        ent1.add_dep(target=ent3)
        ent1.clear_parent_deps()
        self.assertFalse(ent1.has_child_dep('B'))
        self.assertFalse(ent1.has_child_dep('C'))