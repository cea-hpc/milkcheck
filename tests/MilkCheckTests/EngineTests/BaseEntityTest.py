# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
Test cases for the BaseEntity classes.
"""

import unittest

# Classes
from ClusterShell.NodeSet import NodeSet, NodeSetException
from MilkCheck.Engine.BaseEntity import BaseEntity, Dependency
from MilkCheck.Engine.ServiceGroup import ServiceGroup
from MilkCheck.ServiceManager import service_manager_self

# Symbols
from MilkCheck.Engine.BaseEntity import CHECK, REQUIRE_WEAK, REQUIRE
from MilkCheck.Engine.BaseEntity import NO_STATUS, DONE, WAITING_STATUS
from MilkCheck.Engine.BaseEntity import TIMEOUT, DEP_ERROR, ERROR
from MilkCheck.Engine.BaseEntity import WARNING

# Exceptions
from MilkCheck.Engine.BaseEntity import IllegalDependencyTypeError
from MilkCheck.Engine.BaseEntity import DependencyAlreadyReferenced
from MilkCheck.Engine.BaseEntity import UndefinedVariableError
from MilkCheck.Engine.BaseEntity import VariableAlreadyExistError
from MilkCheck.Engine.BaseEntity import InvalidVariableError

import socket
HOSTNAME = socket.gethostname().split('.')[0]

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
        serv_a.status = WARNING
        service.add_dep(serv_a)
        service.add_dep(serv_b, CHECK)
        self.assertEqual(service.eval_deps_status(), NO_STATUS)
        serv_a.status = NO_STATUS
        serv_b.status = WARNING
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
        """Test that eval_deps_status return DEP_ERROR"""
        service = BaseEntity("test_service")
        serv_a = BaseEntity("A")
        serv_b = BaseEntity("B")
        service.add_dep(serv_a)
        service.add_dep(serv_b, CHECK)
        serv_b.status = DONE
        serv_a.status = TIMEOUT
        self.assertEqual(service.eval_deps_status(), DEP_ERROR)

    def test_eval_deps_warnings(self):
        """Test that eval_deps_status return WARNING"""
        service = BaseEntity("test_service")
        serv_a = BaseEntity("A")
        serv_b = BaseEntity("B")
        service.add_dep(serv_a, REQUIRE_WEAK)
        service.add_dep(serv_b, REQUIRE_WEAK)
        serv_b.status = ERROR
        serv_a.status = TIMEOUT
        self.assertEqual(service.eval_deps_status(), WARNING)
        serv_a.status = DONE
        serv_b.status = WARNING
        self.assertEqual(service.eval_deps_status(), WARNING)

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
        self.assertFalse(ent1.has_parent_dep('B'))
        self.assertFalse(ent1.has_parent_dep('C'))

    def test_clear_childs(self):
        '''Test remove all childrens dependencies'''
        ent1 = BaseEntity(name='A')
        ent2 = BaseEntity(name='B')
        ent3 = BaseEntity(name='C')
        ent1.add_dep(target=ent2, parent=False)
        ent1.add_dep(target=ent3, parent=False)
        ent1.clear_child_deps()
        self.assertFalse(ent1.has_child_dep('B'))
        self.assertFalse(ent1.has_child_dep('C'))

    def test_fullname(self):
        '''Test that the property return the fullname of the current entity'''
        ent1 = BaseEntity('alpha')
        self.assertEqual(ent1.fullname(), ent1.name)
        ent2 = BaseEntity('beta')
        ent3 = BaseEntity('gamma')
        ent2.parent = ent3
        ent1.parent = ent2
        self.assertEqual(ent1.fullname(), 'gamma.beta.alpha')

    def test_longname(self):
        """ """
        # No dep, no desc
        ent1 = BaseEntity('alpha')
        self.assertEqual(ent1.longname(), "alpha")

        # Desc, no dep
        ent1.desc = "small description"
        self.assertEqual(ent1.longname(), "alpha - small description")

        # Desc and dep
        ent2 = BaseEntity('beta')
        ent2.desc = "another description"
        ent2.parent = ent1
        self.assertEqual(ent2.longname(), "alpha.beta - another description")
    
    def test_excluded(self):
        """Test the excluded mecanism"""
        ent1 = BaseEntity('E1')
        ent2 = BaseEntity('E2')
        ent3 = BaseEntity('E3')
        
        ent3.add_dep(ent2)

        self.assertFalse(ent1.excluded())
        self.assertTrue(ent1.excluded(["E1"]))
        self.assertTrue(ent3.excluded(["E2"]))

    def test_graph_entity(self):
        """Test the DOT graph output for an entity"""
        ent1 = BaseEntity('E1')
        self.assertEqual(ent1.graph(), '"E1";\n')

class VariableBaseEntityTest(unittest.TestCase):
    """Tests cases for the class variable management methods for BaseEntity."""

    def test_add_variable_twice(self):
        '''Add a variable twice raises VariableAlreadyExistError'''
        svc = BaseEntity('test_var')
        svc.add_var('var', 'foo')
        self.assertRaises(VariableAlreadyExistError, svc.add_var, 'var', 'foo')

    def test_remove_variable(self):
        '''Remove a variable, defined or not, is fine.'''
        svc = BaseEntity('test_var')
        svc.add_var('var', 'foo')
        self.assertEqual(svc._lookup_variable('var'), 'foo')

        # Remove it
        svc.remove_var('var')
        self.assertRaises(UndefinedVariableError, svc._lookup_variable, 'var')

        # Remove it again does not raise an exception.
        svc.remove_var('var')
        self.assertRaises(UndefinedVariableError, svc._lookup_variable, 'var')

    def test_lookup_variables1(self):
        '''Test variables resolution through a single entity'''
        service = BaseEntity('test_service')
        service.add_var('VAR', 'test')
        self.assertEqual(service._lookup_variable('VAR'), 'test')

    def test_lookup_variables2(self):
        '''Test variables resolution through multiple entities'''
        service = BaseEntity('test_service')
        service.add_var('VAR', 'test')
        group = BaseEntity('group_service')
        group.add_var('GVAR', 'group')
        service.parent = group
        self.assertEqual(service._lookup_variable('VAR'), 'test')
        self.assertEqual(service._lookup_variable('GVAR'), 'group')

    def test_lookup_variables3(self):
        '''Test variables resolution with an undefined var'''
        service = BaseEntity('test_service')
        service.add_var('VAR', 'test')
        group = BaseEntity('group_service')
        group.add_var('GVAR', 'group')
        service.parent = group
        self.assertRaises(UndefinedVariableError,
                          service._lookup_variable, 'BAD_VAR')

    def test_lookup_variables4(self):
        '''Test variables resolution with a var referencing a property'''
        service = BaseEntity('test_service')
        service.add_var('VAR', 'test')
        group = BaseEntity('group_service')
        group.add_var('GVAR', 'group')
        service.parent = group
        self.assertEqual(service._lookup_variable('GVAR'), 'group')
        self.assertEqual(service._lookup_variable('TARGET'), None)
        self.assertEqual(service._lookup_variable('NAME'), 'test_service')

    def test_lookup_global_variables(self):
        '''Test global variables resolution'''
        service = BaseEntity('test_service')
        service_manager_self().add_var('MGRVAR', 'test')
        self.assertEqual(service._lookup_variable('MGRVAR'), 'test')

    def test_resolve_value1(self):
        '''Test no replacement to do so just return the initial value'''
        service = BaseEntity('test_service')
        self.assertEqual(service._resolve('hello world'), 'hello world')

    def test_resolve_value2(self):
        '''Test replacement of variable referenced in the entity'''
        service = BaseEntity('test_service')
        service.add_var('NODES', 'localhost,127.0.0.1')
        self.assertEqual(service._resolve('%NODES'), 'localhost,127.0.0.1')

    def test_resolve_value3(self):
        '''Test multiple variable replacements'''
        service = BaseEntity('test_service')
        service.add_var('NODES', 'localhost,127.0.0.1')
        self.assertEqual(service._resolve('%NODES %NAME'),
                         'localhost,127.0.0.1 test_service')

    def test_resolve_value4(self):
        '''Test resolution of an expression'''
        service = BaseEntity('test_service')
        self.assertEqual(service._resolve('%(echo hello world)'),
                         'hello world')

    def test_resolve_value5(self):
        '''Test combining resolution of variables and expressions'''
        service = BaseEntity('test_service')
        service.add_var('NODES', 'localhost,127.0.0.1')
        self.assertEqual(service._resolve('%NODES %(echo hello world) %NAME'),
                         'localhost,127.0.0.1 hello world test_service')

    def test_resolve_value6(self):
        '''Test resolution of variable inside an expression'''
        service = BaseEntity('test_service')
        self.assertEqual(service._resolve('%(echo %NAME)'),
                         'test_service')

    def test_resolve_value7(self):
        '''Test resolution of variable inside an expression (2)'''
        service = BaseEntity('test_service')
        service.add_var('CMD', 'echo')
        self.assertEqual(service._resolve('%(%CMD foo)'), 'foo')

    def test_resolve_value8(self):
        '''Test resolution of invalid variable name'''
        service = BaseEntity('test_service')
        self.assertRaises(ValueError, service._resolve, '%0foo')

    def test_resolve_value9(self):
        '''Test resolution of false command'''
        service = BaseEntity('test_service')
        self.assertRaises(InvalidVariableError, service._resolve, '%(notexist)')

    def test_resolve_compat(self):
        '''Test resolution of an expression (compat mode $)'''
        service = BaseEntity('test_service')
        self.assertEqual(service._resolve('$(echo hello world)'),
                         'hello world')
        self.assertRaises(InvalidVariableError, service._resolve, '$(notexist)')

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
        '''Command substitution with a non-zero exit code should be ok'''
        service = BaseEntity('test_service')
        service.add_var('NODES', '$(/bin/false)')
        self.assertEqual(service._resolve('%NODES'), '')

    def test_resolve_property5(self):
        '''Test resolution with a property containing special characters'''
        service = BaseEntity('test_service')
        service.add_var('NODES', HOSTNAME)
        service.target = '%NODES'
        self.assertEqual(service.resolve_property('target'),
            NodeSet(HOSTNAME))

    def test_resolve_2_variables(self):
        '''Test resolution with two adjacent variables'''
        service = BaseEntity('test_service')
        service.add_var('FOO', 'foo')
        service.add_var('BAR', 'bar')
        self.assertEqual(service._resolve('%FOO%BAR'), 'foobar')

    def test_resolve_escape_char(self):
        '''Test resolution with a variable escaping %'''
        service = BaseEntity('test_service')
        service.add_var('FOO', 'Keep my %%noeval!')
        self.assertEqual(service._resolve('%FOO'), 'Keep my %noeval!')

    def test_resolve_recurse(self):
        '''Test recursive variable resolution'''
        service = BaseEntity('test_service')
        service.add_var('foo', 'key')
        service.add_var('bar', 'Keep my %foo')
        self.assertEqual(service._resolve('%bar'), 'Keep my key')

    def test_resolve_command_substitution(self):
        '''Test command substitution'''
        service = BaseEntity('test_service')
        service.add_var('EXCLUDED_NODES', 'foo')
        self.assertEqual(
            service._resolve(
                 '$([ -n "%EXCLUDED_NODES" ] && echo "-n %EXCLUDED_NODES")'),
            '-n foo')

    def test_resolve_2_command_substitutions(self):
        '''Test 2 command substitutions'''
        service = BaseEntity('test_service')
        service.add_var('EXCLUDED_NODES', 'foo')
        service.add_var('SELECTED_NODES', 'bar')
        self.assertEqual(
            service._resolve(
                 '$([ -n "%SELECTED_NODES" ] && echo "-n %SELECTED_NODES")'
                 + ' $([ -n "%EXCLUDED_NODES" ] && echo "-x %EXCLUDED_NODES")'),
            '-n bar -x foo')

class DependencyTest(unittest.TestCase):
    """Dependency test cases."""

    def test_dependency_instanciation(self):
        """Test instanciation of a dependency."""
        service = BaseEntity("PARENT")
        service = BaseEntity("CHILD")
        self.assertRaises(AssertionError, Dependency, None)
        self.assertRaises(AssertionError, Dependency, service, "TEST")
        self.assertTrue(Dependency(service))
        self.assertTrue(Dependency(service, CHECK))
        self.assertTrue(Dependency(service, CHECK, True))

    def test_is_weak_dependency(self):
        """Test the behaviour of the method is_weak."""
        dep_a = Dependency(BaseEntity("Base"), CHECK)
        dep_b = Dependency(BaseEntity("Base"), REQUIRE)
        dep_c = Dependency(BaseEntity("Base"), REQUIRE_WEAK)
        self.assertFalse(dep_a.is_weak())
        self.assertFalse(dep_b.is_weak())
        self.assertTrue(dep_c.is_weak())

    def test_is_strong_dependency(self):
        """Test the behaviour of is_strong method."""
        dep_a = Dependency(BaseEntity("Base"), CHECK)
        dep_b = Dependency(BaseEntity("Base"), REQUIRE)
        dep_c = Dependency(BaseEntity("Base"), REQUIRE_WEAK)
        self.assertTrue(dep_a.is_strong())
        self.assertTrue(dep_b.is_strong())
        self.assertFalse(dep_c.is_strong())

    def test_is_internal(self):
        """Test the behaviour of the method is internal"""
        dep = Dependency(target=BaseEntity('Group'), intr=True)
        self.assertTrue(dep.is_internal())
        dep = Dependency(target=BaseEntity('Group'), intr=False)
        self.assertFalse(dep.is_internal())


    def test_graph(self):
        """Test the DOT output of a dependency"""
        p_service = BaseEntity("PARENT")
        c_service = BaseEntity("CHILD")
        dep = Dependency(c_service, REQUIRE)
        #self.assertEqual(dep.graph(p_service), '"CHILD" -> "PARENT";\n')
        self.assertEqual(dep.graph(p_service), '"PARENT" -> "CHILD";\n')
        p_group = ServiceGroup('P_Group')
        c_group = ServiceGroup('C_Group')
        p_dep = Dependency(p_group)
        c_dep = Dependency(c_group)
        self.assertEqual(c_dep.graph(p_group),
                        '"P_Group.__hook" -> "C_Group.__hook" '
                        '[ltail="cluster_P_Group",lhead="cluster_C_Group"];\n')
        self.assertEqual(c_dep.graph(p_service), 
                        '"PARENT" -> "C_Group.__hook" '
                        '[lhead="cluster_C_Group"];\n')
        self.assertEqual(dep.graph(p_group),
                        '"P_Group.__hook" -> "CHILD" '
                        '[ltail="cluster_P_Group"];\n')


    def test_graph_dep_type(self):
        """Test the DOT output of a dependency type"""
        ent = BaseEntity("ENTITY")
        dep_c = Dependency(BaseEntity("Base"), CHECK)
        dep_r = Dependency(BaseEntity("Base"), REQUIRE)
        dep_rw = Dependency(BaseEntity("Base"), REQUIRE_WEAK)
        self.assertEqual(dep_c.graph(ent), '"ENTITY" -> "Base";\n')
        self.assertEqual(dep_r.graph(ent), '"ENTITY" -> "Base";\n')
        self.assertEqual(dep_rw.graph(ent), 
                            '"ENTITY" -> "Base" [style=dashed];\n')
