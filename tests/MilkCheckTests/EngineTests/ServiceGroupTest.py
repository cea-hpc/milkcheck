# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

'''
This modules defines the tests cases targeting the ServiceGroup object
'''

from unittest import TestCase

# Classes
from MilkCheck.Engine.ServiceGroup import ServiceGroup
from MilkCheck.Engine.Service import Service
from MilkCheck.Engine.Action import Action
from ClusterShell.NodeSet import NodeSet

# Symbols
from MilkCheck.Engine.BaseEntity import NO_STATUS, DONE, TIMED_OUT
from MilkCheck.Engine.BaseEntity import WAITING_STATUS, ERROR
from MilkCheck.Engine.BaseEntity import DONE_WITH_WARNINGS, TOO_MANY_ERRORS
from MilkCheck.Engine.Dependency import CHECK, REQUIRE_WEAK

class ServiceGroupTest(TestCase):
    '''Define the test cases of a ServiceGroup.'''
    
    def test_instanciation_service_group(self):
        '''Test instanciation of a ServiceGroup.'''
        ser_group = ServiceGroup('GROUP')
        self.assertTrue(ser_group)
        self.assertTrue(isinstance(ser_group, ServiceGroup))
        self.assertEqual(ser_group.name, 'GROUP')

    def test_update_target(self):
        '''Test update of the target of a group of services'''
        grp = ServiceGroup('G')
        srva = Service('A')
        grp.add_inter_dep(target=srva)
        grp.update_target('fortoy[5-10]')
        self.assertTrue(grp.target == NodeSet('fortoy[5-10]'))
        self.assertTrue(srva.target == NodeSet('fortoy[5-10]'))
        
    def test_reset_service_group(self):
        '''Test the ability to reset values of a service group'''
        group = ServiceGroup('GROUP')
        ser1 = Service('I1')
        action = Action(name='start', delay=3)
        action.retry = 5
        action.retry = 3
        action.status = DONE
        ser1.add_action(action)
        ser1.warnings = True
        ser1.status = DONE_WITH_WARNINGS
        group.add_inter_dep(target=ser1)
        group.status = ERROR
        group.reset()
        self.assertEqual(group.status, NO_STATUS)
        self.assertEqual(ser1.status, NO_STATUS)
        self.assertEqual(action.status, NO_STATUS)
        self.assertFalse(ser1.warnings)
        self.assertEqual(action.retry, 5)
        
    def test_search_node_graph(self):
        """Test search node in a graph trough a ServiceGroup"""
        group = ServiceGroup('GROUP')
        ser1 = Service('I1')
        ser2 = Service('I2')
        eser1 = Service('E1')
        eser2 = Service('E2')
        eser3 = Service('E3')
        group.add_inter_dep(target=ser1)
        group.add_inter_dep(target=ser2)
        group.add_dep(target=eser1, parent=False)
        group.add_dep(target=eser2)
        group.add_dep(target=eser3)
        self.assertTrue(group.search('I1'))
        self.assertTrue(group.search('E2'))
        self.assertTrue(eser1.search('I1'))
        self.assertTrue(eser1.search('E3'))
        self.assertFalse(group.search('E0'))
        
    def test_add_dep_service_group(self):
        '''Test ability to add dependencies to a ServiceGroup'''
        ser_group = ServiceGroup('GROUP')
        s1 = Service('alpha')
        s1.add_action(Action('start', 'localhost', '/bin/true'))
        s2 = Service('beta')
        s2.add_action(Action('action', 'localhost', '/bin/true'))
        s3 = Service('lambda')
        ser_group.add_inter_dep(target=s1)
        ser_group.add_inter_dep(target=s2)
        ser_group.add_dep(target=s3)
        self.assertTrue(ser_group.has_action('start'))
        self.assertTrue(ser_group.has_action('action'))
        self.assertTrue(s1.name in ser_group._source.parents)
        self.assertTrue(s1.name in ser_group._sink.children)
        self.assertTrue(s2.name in ser_group._source.parents)
        self.assertTrue(s2.name in ser_group._sink.children)
        self.assertFalse(s3.name in ser_group.children)
        self.assertTrue(s3.name in ser_group.parents)
        s4 = Service('theta')
        s4.add_action(Action('fire', 'localhost','/bin/true'))
        ser_group.add_dep(target=s4, parent=False)
        self.assertTrue(s4.name in ser_group.children)
        self.assertTrue(s4.has_parent_dep(ser_group.name))

    def test_add_inter_dep_service_group_first(self):
        '''Test ability to add dependencies to the subgraph N1'''
        group = ServiceGroup('GROUP')
        s1 = Service('alpha')
        s2 = Service('beta')
        s3 = Service('lambda')
        group.add_inter_dep(target=s1)
        group.add_inter_dep(base=s1 ,target=s2)
        group.add_inter_dep(target=s3)
        self.assertTrue(group.has_subservice('alpha'))
        self.assertTrue(group.has_subservice('beta'))
        self.assertTrue(group.has_subservice('lambda'))
        self.assertTrue(s2.has_parent_dep('sink'))
        self.assertFalse(s2.has_child_dep('source'))
        self.assertFalse(s1.has_parent_dep('sink'))
        self.assertTrue(s1.has_child_dep('source'))
        self.assertTrue(s3.has_child_dep('source'))
        self.assertTrue(s3.has_parent_dep('sink'))

    def test_add_inter_dep_service_group_second(self):
        '''Test ability to add dependencies to the subgraph N2'''
        group = ServiceGroup('GROUP')
        s1 = Service('alpha')
        s2 = Service('beta')
        s3 = Service('lambda')
        group.add_inter_dep(target=s1)
        group.add_inter_dep(base=s1 ,target=s2)
        group.add_inter_dep(target=s3)
        group.add_inter_dep(base=s1, target=s3)
        self.assertTrue(s1.has_parent_dep('beta'))
        self.assertTrue(s1.has_parent_dep('lambda'))
        self.assertTrue(s1.has_child_dep('source'))
        self.assertTrue(s2.has_child_dep('alpha'))
        self.assertTrue(s3.has_child_dep('alpha'))
        self.assertTrue(s2.has_parent_dep('sink'))
        self.assertTrue(s3.has_parent_dep('sink'))

    def test_add_inter_dep_service_group_third(self):
        '''Test ability to add dependencies to the subgraph N3'''
        group = ServiceGroup('GROUP')
        s1 = Service('alpha')
        s2 = Service('beta')
        s3 = Service('lambda')
        group.add_inter_dep(target=s1)
        group.add_inter_dep(target=s2)
        group.add_inter_dep(target=s3)
        group.add_inter_dep(base=s1, target=s3)
        group.add_inter_dep(base=s2, target=s3)
        self.assertTrue(s1.has_child_dep('source'))
        self.assertFalse(s1.has_parent_dep('sink'))
        self.assertTrue(s1.has_parent_dep('lambda'))
        self.assertTrue(s2.has_child_dep('source'))
        self.assertFalse(s2.has_parent_dep('sink'))
        self.assertTrue(s2.has_parent_dep('lambda'))
        self.assertTrue(s3.has_child_dep('alpha'))
        self.assertTrue(s3.has_child_dep('beta'))
        self.assertTrue(s3.has_parent_dep('sink'))
        self.assertFalse(s3.has_child_dep('source'))

    def test_remove_inter_dep(self):
        '''Test ability to remove a dependency in a subgraph'''
        group = ServiceGroup('GROUP')
        s1 = Service('alpha')
        s2 = Service('beta')
        s3 = Service('lambda')
        group.add_inter_dep(target=s1)
        group.add_inter_dep(target=s2)
        group.add_inter_dep(target=s3)
        group.add_inter_dep(base=s1, target=s3)
        group.add_inter_dep(base=s2, target=s3)
        group.remove_inter_dep('lambda')
        self.assertTrue(s1.has_parent_dep('sink'))
        self.assertTrue(s2.has_parent_dep('sink'))
        self.assertTrue(s1.has_child_dep('source'))
        self.assertTrue(s2.has_child_dep('source'))
        self.assertFalse(s1.has_parent_dep('lambda'))
        self.assertFalse(s2.has_parent_dep('lambda'))
        group.remove_inter_dep('alpha')
        self.assertFalse(group._source.has_parent_dep('alpha'))
        self.assertTrue(group._source.has_parent_dep('beta'))
        self.assertFalse(group._sink.has_child_dep('alpha'))
        self.assertTrue(group._sink.has_child_dep('beta'))
        group.remove_inter_dep('beta')
        self.assertFalse(group._source.parents)
        self.assertFalse(group._sink.children)
        
    def test_has_subservice(self):
        '''Test whether a service is an internal dependency of a group'''
        group = ServiceGroup('group')
        serv = Service('intern_service')
        self.assertFalse(group.has_subservice(serv.name))
        group.add_inter_dep(target=serv)
        self.assertTrue(group.has_subservice(serv.name))

    
    def test_search_deps(self):
        '''Test the method search deps overriden from BaseEntity.'''
        group = ServiceGroup('GROUP')
        serv = Service('SERVICE')
        group_dep =  ServiceGroup('GROUP2')
        deps = group.search_deps([NO_STATUS])
        self.assertEqual(len(deps['internal']), 0)
        group.add_inter_dep(target=serv)
        group.add_dep(target=group_dep)
        serva = Service('A')
        serva.status = DONE
        group.add_dep(target=serva)
        deps = group.search_deps([NO_STATUS])
        self.assertEqual(len(deps['external']), 1)
        self.assertEqual(len(deps['internal']), 1)
        deps = group.search_deps([NO_STATUS, DONE])
        self.assertEqual(len(deps['external']), 2)
        self.assertEqual(len(deps['internal']), 1)
        
    def test_eval_deps_status_done(self):
        '''Test the method eval_deps_status NO_STATUS'''
        group = ServiceGroup('group')
        e1 = Service('E1')
        e2 = Service('E2')
        group.add_dep(target=e1)
        group.add_dep(target=e2)
        group.add_inter_dep(target=Service('I1'))
        self.assertEqual(group.eval_deps_status(), NO_STATUS)
        e1.status = DONE
        e2.status = DONE
        self.assertEqual(group.eval_deps_status(), NO_STATUS)

    def test_eval_deps_status_error(self):
        '''Test the method eval_deps_status ERROR'''
        group = ServiceGroup('group')
        e1 = Service('E1')
        e2 = Service('E2')
        e1.status = ERROR
        group.add_dep(target=e1)
        group.add_dep(target=e2)
        group.add_inter_dep(target=Service('I1'))
        self.assertEqual(group.eval_deps_status(), ERROR)
        self.assertEqual(group.eval_deps_status(), ERROR)

    def test_eval_deps_status_ws(self):
        '''Test the method eval_deps_status WAITING_STATUS'''
        group = ServiceGroup('group')
        e1 = Service('E1')
        e2 = Service('E2')
        e1.status = DONE
        e2.status = DONE_WITH_WARNINGS
        group.add_dep(target=e1)
        group.add_dep(target=e2)
        group._source.status = WAITING_STATUS
        self.assertEqual(group.eval_deps_status(), WAITING_STATUS)

    def test_set_algo_reversed(self):
        '''Test updates dependencies in changing the reversed flag'''
        group = ServiceGroup('group')
        self.assertTrue(group._source.has_child_dep('group'))
        self.assertFalse(group._sink.has_parent_dep('group'))
        group.algo_reversed = True
        self.assertFalse(group._source.has_child_dep('group'))
        self.assertTrue(group._sink.has_parent_dep('group'))
        group.algo_reversed = False
        self.assertTrue(group._source.has_child_dep('group'))
        self.assertFalse(group._sink.has_parent_dep('group'))

    def test_prepare_empty_group(self):
        '''Test method prepare with a single empty ServiceGroup.'''
        group = ServiceGroup('GROUP')
        group.run('start')
        self.assertEqual(group.status, DONE)

    def test_prepare_empty_group_reverse(self):
        '''Test method prepare reverse with a single empty ServiceGroup.'''
        group = ServiceGroup('GROUP')
        group.algo_reversed = True
        group.run('start')
        self.assertEqual(group.status, DONE)

    def test_prepare_group_subservice(self):
        '''Test prepare group with an internal dependency.'''
        group = ServiceGroup('GROUP')
        subserv = Service('SUB1')
        subserv.add_action(Action('start', 'localhost', '/bin/true'))
        group.add_inter_dep(target=subserv)
        group.run('start')
        self.assertEqual(group.status, DONE)
        self.assertEqual(subserv.status, DONE)

    def test_prepare_group_subservice_reverse(self):
        '''Test prepare reverse group with an internal dependency.'''
        group = ServiceGroup('GROUP')
        group.algo_reversed = True
        subserv = Service('SUB1')
        subserv.algo_reversed = True
        subserv.add_action(Action('start', 'localhost', '/bin/true'))
        group.add_inter_dep(target=subserv)
        group.run('start')
        self.assertEqual(group.status, DONE)
        self.assertEqual(subserv.status, DONE)
    
    def test_prepare_group_subservices(self):
        '''Test prepare group with multiple internal dependencies.'''
        group = ServiceGroup('GROUP')
        ac_suc1 = Action('start', 'localhost', '/bin/true')
        ac_suc2 = Action('start', 'localhost', '/bin/true')
        ac_suc3 = Action('start', 'localhost', '/bin/true')
        
        subserv_a = Service('SUB1')
        subserv_b = Service('SUB2')
        subserv_c = Service('SUB3')
        
        subserv_a.add_action(ac_suc1)
        subserv_b.add_action(ac_suc2)
        subserv_c.add_action(ac_suc3)

        group.add_inter_dep(target=subserv_a)
        group.add_inter_dep(target=subserv_b)
        group.add_inter_dep(base=subserv_a, target=subserv_c)
        group.add_inter_dep(base=subserv_b, target=subserv_c)

        group.run('start')
        self.assertEqual(group.status, DONE)
        self.assertEqual(subserv_a.status, DONE)
        self.assertEqual(subserv_b.status, DONE)
        self.assertEqual(subserv_c.status, DONE)
        
    def test_prepare_empty_group_external_deps(self):
        '''Test prepare an empty group with a single external dependency.'''
        group = ServiceGroup('GROUP')
        ext_serv = Service('EXT_SERV')
        ac_suc = Action('start', 'localhost', '/bin/true')
        ext_serv.add_action(ac_suc)
        group.add_dep(ext_serv)
        group.run('start')
        self.assertEqual(group.status, DONE)
        self.assertEqual(ext_serv.status, DONE)
    
    def test_prepare_group_internal_external_deps(self):
        '''Test prepare a group with internal and external dependencies'''
        # Group
        group = ServiceGroup('GROUP')
        # Internal
        inter_serv1 = Service('INT_SERV1')
        inter_serv2 = Service('INT_SERV2')
        inter_serv3 = Service('INT_SERV3')
        # External
        ext_serv1 =  Service('EXT_SERV1')
        ext_serv2 = Service('EXT_SERV2')
        ac_suc1 = Action('start', 'localhost', '/bin/true')
        ac_suc2 = Action('start', 'localhost', '/bin/true')
        ac_suc3 = Action('start', 'localhost', '/bin/true')
        ac_suc4 = Action('start', 'localhost', '/bin/true')
        ac_suc5 = Action('start', 'localhost', '/bin/true')
        # Add actions
        inter_serv1.add_action(ac_suc1)
        inter_serv2.add_action(ac_suc2)
        inter_serv3.add_action(ac_suc3)
        ext_serv1.add_action(ac_suc4)
        ext_serv2.add_action(ac_suc5)
        # Add dependencies
        group.add_inter_dep(target=inter_serv1)
        group.add_inter_dep(target=inter_serv2)
        group.add_inter_dep(base=inter_serv2, target=inter_serv3)
        group.add_dep(ext_serv1)
        group.add_dep(ext_serv2)
        # Prepare group
        group.run('start')
        self.assertEqual(group.status, DONE)
        self.assertEqual(ext_serv1.status, DONE)
        self.assertEqual(ext_serv2.status, DONE)
        self.assertEqual(inter_serv1.status, DONE)
        self.assertEqual(inter_serv2.status, DONE)
        self.assertEqual(inter_serv3.status, DONE)

    def test_prepare_group_with_errors_one(self):
        '''Test prepare a group terminated by DONE_WITH_WARNINGS'''
        # Group
        group = ServiceGroup('GROUP')
        # Internal
        inter_serv1 = Service('INT_SERV1')
        inter_serv2 = Service('INT_SERV2')
        inter_serv3 = Service('INT_SERV3')
        # External
        ext_serv1 =  Service('EXT_SERV1')
        ext_serv2 = Service('EXT_SERV2')
        ac_suc1 = Action('start', 'localhost', '/bin/true')
        ac_suc2 = Action('start', 'localhost', '/bin/true')
        ac_suc3 = Action('start', 'localhost', '/bin/true')
        ac_err1 = Action('start', 'localhost', '/bin/false')
        ac_err2 = Action('start', 'localhost', '/bin/false')
        # Add actions
        inter_serv1.add_action(ac_suc1)
        inter_serv2.add_action(ac_suc2)
        inter_serv3.add_action(ac_err1)
        ext_serv1.add_action(ac_suc3)
        ext_serv2.add_action(ac_err2)
        # Add dependencies
        group.add_inter_dep(target=inter_serv1)
        group.add_inter_dep(target=inter_serv2)
        group.add_inter_dep(base=inter_serv2, target=inter_serv3,
            sgth=REQUIRE_WEAK)
        group.add_dep(ext_serv1)
        group.add_dep(target=ext_serv2, sgth=REQUIRE_WEAK)
        # Prepare group
        group.run('start')
        self.assertEqual(group.status, DONE_WITH_WARNINGS)
        self.assertEqual(ext_serv1.status, DONE)
        self.assertEqual(ext_serv2.status, TOO_MANY_ERRORS)
        self.assertEqual(inter_serv1.status, DONE)
        self.assertEqual(inter_serv2.status, DONE_WITH_WARNINGS)
        self.assertEqual(inter_serv3.status, TOO_MANY_ERRORS)

    def test_prepare_group_with_errors_two(self):
        '''Test prepare a group terminated by ERROR'''
        # Group
        group = ServiceGroup('GROUP')
        # Internal
        inter_serv1 = Service('INT_SERV1')
        inter_serv2 = Service('INT_SERV2')
        inter_serv3 = Service('INT_SERV3')
        # External
        ext_serv1 =  Service('EXT_SERV1')
        ext_serv2 = Service('EXT_SERV2')
        ac_suc1 = Action('start', 'localhost', '/bin/true')
        ac_suc2 = Action('start', 'localhost', '/bin/true')
        ac_suc3 = Action('start', 'localhost', '/bin/true')
        ac_err = Action('start', 'localhost', '/bin/false')
        ac_err_chk = Action('status', 'localhost', '/bin/false')
        # Add actions
        inter_serv1.add_action(ac_suc1)
        inter_serv2.add_action(ac_suc2)
        inter_serv3.add_action(ac_err_chk)
        ext_serv1.add_action(ac_suc3)
        ext_serv2.add_action(ac_err)
        # Add dependencies
        group.add_inter_dep(target=inter_serv1)
        group.add_inter_dep(target=inter_serv2)
        group.add_inter_dep(base=inter_serv2, target=inter_serv3, sgth=CHECK)
        group.add_dep(ext_serv1)
        group.add_dep(target=ext_serv2, sgth=REQUIRE_WEAK)
        # Prepare group
        group.run('start')
        self.assertEqual(group.status, ERROR)
        self.assertEqual(ext_serv1.status, DONE)
        self.assertEqual(ext_serv2.status, TOO_MANY_ERRORS)
        self.assertEqual(inter_serv1.status, DONE)
        self.assertEqual(inter_serv2.status, ERROR)
        self.assertEqual(inter_serv3.status, TOO_MANY_ERRORS)
        
    def test_run_partial_deps(self):
        '''Test stop algorithm as soon as the calling point is done.'''
        serv = Service('NOT_CALLED')
        serv_a = ServiceGroup('CALLING_GROUP')
        serv_b = Service('SERV_1')
        serv_c = Service('SERV_2')
        act_suc1 = Action('start', 'localhost', '/bin/true')
        act_suc2 = Action('start', 'localhost', '/bin/true')
        serv_b.add_action(act_suc1)
        serv_c.add_action(act_suc2)
        serv.add_dep(serv_a)
        serv_a.add_dep(target=serv_b)
        serv_a.add_inter_dep(target=serv_c)
        serv_a.run('start')
        self.assertEqual(serv.status, NO_STATUS)
        self.assertEqual(serv_a.status, DONE)
        self.assertEqual(serv_b.status, DONE)
        self.assertEqual(serv_c.status, DONE)