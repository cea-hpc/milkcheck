#
# Copyright CEA (2011-2017)
#

'''
This modules defines the tests cases targeting the ServiceGroup object
'''

import socket
from unittest import TestCase

# Classes
from MilkCheck.Engine.Action import Action
from MilkCheck.Engine.ServiceGroup import ServiceGroup, ServiceNotFoundError
from MilkCheck.Engine.Service import Service
from ClusterShell.NodeSet import NodeSet

# Symbols
from MilkCheck.Engine.BaseEntity import NO_STATUS, DONE, SKIPPED, MISSING
from MilkCheck.Engine.BaseEntity import WAITING_STATUS, DEP_ERROR
from MilkCheck.Engine.BaseEntity import WARNING, ERROR
from MilkCheck.Engine.BaseEntity import CHECK, REQUIRE_WEAK, REQUIRE, FILTER
from MilkCheck.Engine.BaseEntity import UnknownDependencyError

HOSTNAME = socket.gethostname().split('.')[0]

class ServiceGroupTest(TestCase):
    '''Define the test cases of a ServiceGroup.'''

    def test_instanciation_service_group(self):
        '''Test instanciation of a ServiceGroup.'''
        ser_group = ServiceGroup('GROUP')
        self.assertTrue(ser_group)
        self.assertTrue(isinstance(ser_group, ServiceGroup))
        self.assertEqual(ser_group.name, 'GROUP')

    def test_add_bad_inter_dep(self):
        """Adding a subservice on a bad base raises an Exception"""
        grp = ServiceGroup('grp')
        srv1 = Service('foo1')
        srv2 = Service('foo2')
        self.assertRaises(ServiceNotFoundError, grp.add_inter_dep,
                          target=srv2, base=srv1)

    def test_inheritance(self):
        """Test inheritance between services"""
        ser = Service('parent')
        ser.target = '127.0.0.1'
        ser.timeout = 15
        group = ServiceGroup('group')
        subser1 = Service('subser1')
        subser1.target = HOSTNAME
        subser2 = Service('subser2')
        subser2.timeout = 3
        group.add_inter_dep(target=subser1)
        group.add_inter_dep(target=subser2)
        group.inherits_from(ser)
        self.assertEqual(group.target, NodeSet('127.0.0.1'))
        self.assertEqual(group.timeout, 15)
        self.assertEqual(subser1.target, NodeSet(HOSTNAME))
        self.assertEqual(subser1.timeout, 15)
        self.assertEqual(subser2.target, NodeSet('127.0.0.1'))
        self.assertEqual(subser2.timeout, 3)

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
        action.maxretry = 5
        action.tries = 3
        action.status = DONE
        ser1.add_action(action)
        ser1.status = ERROR
        group.add_inter_dep(target=ser1)
        group.status = DEP_ERROR
        group.reset()
        self.assertEqual(group.status, NO_STATUS)
        self.assertEqual(ser1.status, NO_STATUS)
        self.assertEqual(action.status, NO_STATUS)
        self.assertEqual(action.tries, 0)

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

    def test_search_node_graph_with_dot(self):
        """Test search node in a graph trough a ServiceGroup"""
        group = ServiceGroup('GROUP')
        ser1 = Service('I1.a')
        ser2 = Service('I2')
        eser1 = Service('E1')
        eser2 = Service('E2.b')
        eser3 = Service('E3.c')
        group.add_inter_dep(target=ser1)
        group.add_inter_dep(target=ser2)
        group.add_dep(target=eser1, parent=False)
        group.add_dep(target=eser2)
        group.add_dep(target=eser3)
        self.assertTrue(group.search('I1.a'))
        self.assertTrue(group.search('E2.b'))
        self.assertTrue(eser1.search('I1.a'))
        self.assertTrue(eser1.search('E3.c'))
        self.assertFalse(group.search('E0.d'))

    def test_search_node_graph_with_dot_and_external(self):
        """Test search node in a graph trough a ServiceGroup"""
        group = ServiceGroup('group', root=True)
        group1 = ServiceGroup('GROUP1')
        ser1 = Service('I1')
        ser2 = Service('I2')
        group2 = ServiceGroup('GROUP2')
        group.add_inter_dep(target=group1)
        group.add_inter_dep(target=group2)
        eser1 = Service('I3')
        eser2 = Service('I4')
        eser3 = Service('I5')
        group1.add_inter_dep(target=ser1)
        group1.add_inter_dep(target=ser2)
        group2.add_inter_dep(target=eser1)
        group2.add_inter_dep(target=eser2)
        group2.add_inter_dep(target=eser3)
        self.assertTrue(group1.search('I1'))
        self.assertTrue(group1.search('I2'))
        self.assertTrue(group2.search('I3'))
        self.assertTrue(group2.search('I4'))
        self.assertTrue(group2.search('I5'))
        self.assertFalse(group2.search('I1'))
        self.assertFalse(group2.search('I2'))
        self.assertTrue(group2.search('GROUP1.I1'))
        self.assertTrue(group2.search('GROUP1.I2'))
        self.assertTrue(group2.search('GROUP1.I1'))
        self.assertTrue(group2.search('GROUP1.I2'))

    def test_add_dep_service_group(self):
        '''Test ability to add dependencies to a ServiceGroup'''
        ser_group = ServiceGroup('GROUP')
        s1 = Service('alpha')
        s1.add_action(Action('start', HOSTNAME, '/bin/true'))
        s2 = Service('beta')
        s2.add_action(Action('action', HOSTNAME, '/bin/true'))
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
        s4.add_action(Action('fire', HOSTNAME,'/bin/true'))
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
        group.add_inter_dep(base=s1, target=s2)
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
        group.add_inter_dep(base=s1, target=s2)
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

    def test_remove_inter_bad_dep(self):
        """Remove a non-existant sub-services raises an Exception"""
        grp = ServiceGroup('group')
        self.assertRaises(ServiceNotFoundError, grp.remove_inter_dep, 'foo')

    def test_has_subservice(self):
        '''Test whether a service is an internal dependency of a group'''
        group = ServiceGroup('group')
        serv = Service('intern_service')
        self.assertFalse(group.has_subservice(serv.name))
        group.add_inter_dep(target=serv)
        self.assertTrue(group.has_subservice(serv.name))

    def test_skip(self):
        """Test skip method for ServiceGroup"""
        grp = ServiceGroup('group')
        srv = Service('skipped')
        srv.add_action(Action('start', target=NodeSet('foo'),
                              command='/bin/true'))
        grp.add_inter_dep(target=srv)
        self.assertFalse(grp.to_skip('start'))
        grp.skip()
        self.assertTrue(grp.to_skip('start'))

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
        '''Test the method eval_deps_status DEP_ERROR'''
        group = ServiceGroup('group')
        e1 = Service('E1')
        e2 = Service('E2')
        e1.status = DEP_ERROR
        group.add_dep(target=e1)
        group.add_dep(target=e2)
        group.add_inter_dep(target=Service('I1'))
        self.assertEqual(group.eval_deps_status(), DEP_ERROR)
        self.assertEqual(group.eval_deps_status(), DEP_ERROR)

    def test_eval_deps_status_ws(self):
        '''Test the method eval_deps_status WAITING_STATUS'''
        group = ServiceGroup('group')
        ext1 = Service('E1')
        ext2 = Service('E2')
        ext1.status = DONE
        ext2.status = WARNING
        group.add_dep(target=ext1)
        group.add_dep(target=ext2)
        int1 = Service('E1')
        group.add_inter_dep(target=int1)
        int1.status = WAITING_STATUS
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
        self.assertEqual(group.status, MISSING)

    def test_prepare_empty_group_reverse(self):
        '''Test method prepare reverse with a single empty ServiceGroup.'''
        group = ServiceGroup('GROUP')
        group.algo_reversed = True
        group.run('start')
        self.assertEqual(group.status, MISSING)

    def test_prepare_group_subservice(self):
        '''Test prepare group with an internal dependency.'''
        group = ServiceGroup('GROUP')
        subserv = Service('SUB1')
        subserv.add_action(Action('start', command='/bin/true'))
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
        subserv.add_action(Action('start', command='/bin/true'))
        group.add_inter_dep(target=subserv)
        group.run('start')
        self.assertEqual(group.status, DONE)
        self.assertEqual(subserv.status, DONE)

    def test_prepare_group_subservices(self):
        '''Test prepare group with multiple internal dependencies.'''
        group = ServiceGroup('GROUP')
        ac_suc1 = Action('start', command='/bin/true')
        ac_suc2 = Action('start', command='/bin/true')
        ac_suc3 = Action('start', command='/bin/true')

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
        ac_suc = Action('start', command='/bin/true')
        ext_serv.add_action(ac_suc)
        group.add_dep(ext_serv)
        group.run('start')
        self.assertEqual(ext_serv.status, DONE)
        self.assertEqual(group.status, MISSING)

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
        ac_suc1 = Action('start', command='/bin/true')
        ac_suc2 = Action('start', command='/bin/true')
        ac_suc3 = Action('start', command='/bin/true')
        ac_suc4 = Action('start', command='/bin/true')
        ac_suc5 = Action('start', command='/bin/true')
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
        '''Test prepare a group terminated by WARNING'''
        # Group
        group = ServiceGroup('GROUP')
        # Internal
        inter_serv1 = Service('INT_SERV1')
        inter_serv2 = Service('INT_SERV2')
        inter_serv3 = Service('INT_SERV3')
        # External
        ext_serv1 =  Service('EXT_SERV1')
        ext_serv2 = Service('EXT_SERV2')
        ac_suc1 = Action('start', command='/bin/true')
        ac_suc2 = Action('start', command='/bin/true')
        ac_suc3 = Action('start', command='/bin/true')
        ac_err1 = Action('start', command='/bin/false')
        ac_err2 = Action('start', command='/bin/false')
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
        self.assertEqual(group.status, DONE)
        self.assertEqual(ext_serv1.status, DONE)
        self.assertEqual(ext_serv2.status, ERROR)
        self.assertEqual(inter_serv1.status, DONE)
        self.assertEqual(inter_serv2.status, DONE)
        self.assertEqual(inter_serv3.status, ERROR)

    def test_prepare_group_with_errors_two(self):
        '''Test prepare a group terminated by DEP_ERROR'''
        # Group
        group = ServiceGroup('GROUP')
        # Internal
        inter_serv1 = Service('INT_SERV1')
        inter_serv2 = Service('INT_SERV2')
        inter_serv3 = Service('INT_SERV3')
        # External
        ext_serv1 =  Service('EXT_SERV1')
        ext_serv2 = Service('EXT_SERV2')
        ac_suc1 = Action('start', command='/bin/true')
        ac_suc2 = Action('start', command='/bin/true')
        ac_suc3 = Action('start', command='/bin/true')
        ac_err = Action('start', command='/bin/false')
        ac_err_chk = Action('status', command='/bin/false')
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
        self.assertEqual(group.status, DEP_ERROR)
        self.assertEqual(ext_serv1.status, DONE)
        self.assertEqual(ext_serv2.status, ERROR)
        self.assertEqual(inter_serv1.status, DONE)
        self.assertEqual(inter_serv2.status, DEP_ERROR)
        self.assertEqual(inter_serv3.status, ERROR)

    def test_run_partial_deps(self):
        '''Test start algorithm as soon as the calling point is done.'''
        serv = Service('NOT_CALLED')
        serv_a = ServiceGroup('CALLING_GROUP')
        serv_b = Service('SERV_1')
        serv_c = Service('SERV_2')
        act_suc1 = Action('start', command='/bin/true')
        act_suc2 = Action('start', command='/bin/true')
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

    def test_run_stop_on_group(self):
        '''Test stop algorithm on a group'''
        group = ServiceGroup('G1')
        i1 = Service('I1')
        i1.add_action(Action('stop', command='/bin/true'))
        group.add_inter_dep(target=i1)
        s1 = Service('S1')
        s1.add_action(Action('stop', command='/bin/true'))
        s1.add_dep(target=group)
        s1.algo_reversed = True
        group.algo_reversed = True
        group.run('stop')
        self.assertEqual(s1.status, DONE)
        self.assertEqual(i1.status, DONE)
        self.assertEqual(group.status, DONE)

    def test_skipped_group(self):
        """A group with only SKIPPED services should be SKIPPED"""
        grp = ServiceGroup('group')
        svc1 = Service('svc1')
        svc1.add_action(Action('start', target="@NOTHING", command=':'))
        svc2 = Service('svc2')
        svc2.add_action(Action('start', target="@NOTHING", command=':'))
        grp.add_inter_dep(target=svc1)
        grp.add_inter_dep(target=svc2)
        grp.run('start')
        self.assertEqual(grp.status, SKIPPED)

    def test_skipped_group_dep_error(self):
        """A full SKIPPED service group with DEP_ERROR should be SKIPPED"""
        svc = Service('error')
        svc.add_action(Action('start', command='/bin/false'))
        grp = ServiceGroup('group')
        svc1 = Service('svc1')
        svc1.add_action(Action('start', target="@NOTHING", command=':'))
        svc2 = Service('svc2')
        svc2.add_action(Action('start', target="@NOTHING", command=':'))
        grp.add_inter_dep(target=svc1)
        grp.add_inter_dep(target=svc2)
        grp.add_dep(svc, sgth=REQUIRE)

        grp.run('start')
        self.assertEqual(svc.status, ERROR)
        self.assertEqual(grp.status, SKIPPED)

    def test_missing_group(self):
        """A group with only MISSING services should be MISSING"""
        grp = ServiceGroup('group')
        svc1 = Service('svc1')
        svc1.add_action(Action('stop', command='/bin/true'))
        grp.add_inter_dep(target=svc1)
        grp.run('start')
        self.assertEqual(grp.status, MISSING)

    def test_group_with_weak_dep_error(self):
        """A group with a weak dep error runs fine (add_inter_dep())."""

        dep1 = Service('dep1')
        dep1.add_action(Action('stop', command='/bin/false'))

        grp = ServiceGroup('group')
        svc = Service('svc')
        svc.add_action(Action('stop', command='/bin/true'))
        grp.add_inter_dep(svc)
        grp.add_dep(dep1, sgth=REQUIRE_WEAK)
        grp.run('stop')

        self.assertEqual(grp.status, DONE)

    def test_filter(self):
        """ServiceGroup supports filter dependency"""
        dep = Service('dep')
        dep.add_action(Action('stop', command='/bin/false', target=HOSTNAME))

        grp = ServiceGroup('group')
        svc = Service('svc')
        svc.add_action(Action('stop', command='/bin/true', target=HOSTNAME))
        grp.add_inter_dep(svc)
        grp.add_dep(dep, sgth=FILTER)
        grp.run('stop')

        self.assertEqual(dep.status, ERROR)
        self.assertEqual(svc.status, SKIPPED)
        self.assertEqual(grp.status, SKIPPED)

    def test_filter_from_service_group(self):
        """a service can filter error nodes from a service group"""
        nodes = "%s,BADNODE" % HOSTNAME

        grp = ServiceGroup('group')
        subsvc = Service('subsvc')
        subsvc.add_action(Action('stop', command='/bin/true', target=nodes))
        grp.add_inter_dep(subsvc)

        svc = Service('svc')
        svc.add_action(Action('stop', command='/bin/true', target=nodes))
        svc.add_dep(grp, sgth=FILTER)
        svc.run('stop')

        self.assertEqual(subsvc.status, ERROR)
        self.assertEqual(grp.status, DEP_ERROR)
        self.assertEqual(svc.status, DONE)

    def test_mix_require_filter_from_service_group(self):
        """mixing filter and require to a failed service group is ok"""
        nodes = "%s,BADNODE" % HOSTNAME

        grp = ServiceGroup('group')
        subsvc = Service('subsvc')
        subsvc.add_action(Action('stop', command='/bin/true', target=nodes))
        grp.add_inter_dep(subsvc)

        svc1 = Service('svc_require')
        svc1.add_action(Action('stop', command='/bin/true', target=nodes))
        svc1.add_dep(grp, sgth=REQUIRE)

        svc2 = Service('svc_filter')
        svc2.add_action(Action('stop', command='/bin/true', target=nodes))
        svc2.add_dep(grp, sgth=FILTER)

        svc3 = Service('svc_before')
        svc3.add_action(Action('stop', command='/bin/true', target=nodes))
        svc3.add_dep(grp, sgth=REQUIRE_WEAK)

        stop = Service('stop')
        stop.add_action(Action('stop', command='/bin/true', target=nodes))
        stop.add_dep(svc1)
        stop.add_dep(svc2)
        stop.add_dep(svc3)
        stop.run('stop')

        self.assertEqual(subsvc.status, ERROR)
        self.assertEqual(grp.status, DEP_ERROR)
        self.assertEqual(svc1.status, DEP_ERROR)
        self.assertEqual(svc2.status, DONE)
        self.assertEqual(svc3.status, ERROR)
        self.assertEqual(stop.status, DEP_ERROR)

    def test_graph_entity(self):
        """Test the DOT graph output"""
        grp = ServiceGroup('Group')
        self.assertEqual(grp.graph(), 'subgraph "cluster_Group" {\nlabel="Group";\nstyle=rounded;\nnode [style=filled];\n"Group.__hook" [style=invis];\n}\n')

    def test_graph_in_graph(self):
        """Test the DOT graph output with a servicegroup within a servicegroup"""
        grp = ServiceGroup('Group')
        subgrp = ServiceGroup('subGroup')
        grp.add_inter_dep(subgrp)
        self.assertEqual(grp.graph(), 'subgraph "cluster_Group" {\nlabel="Group";\nstyle=rounded;\nnode [style=filled];\n"Group.__hook" [style=invis];\nsubgraph "cluster_Group.subGroup" {\nlabel="Group.subGroup";\nstyle=rounded;\nnode [style=filled];\n"Group.subGroup.__hook" [style=invis];\n}\n}\n')


class ServiceGroupFromDictTest(TestCase):
    '''Test cases of ServiceGroup.fromdict()'''

    def test_fromdict1(self):
        '''Test instanciation of a service group from a dictionnary'''
        sergrp = ServiceGroup('S1')
        sergrp.fromdict(
           {'services':
                {'hpss_nfs':
                    {'target': 'localhost',
                     'actions':
                        {'start': {'cmd': '/bin/True'},
                        'stop': {'cmd': '/bin/False'}},
                        'desc': "I'm the service hpss_nfs"
                     },
                 'lustre':
                     {'target': 'localhost',
                      'actions':
                        {'start': {'cmd':'/bin/True'},
                         'stop': {'cmd': '/bin/False'}},
                      'desc': "I'm the service lustre"}},
            'desc': "I'm the service S1",
            'target': 'localhost',
            'variables':{
                'var1': 'toto',
                'var2': 'titi'
            },
        })

        self.assertEqual(len(sergrp.variables), 2)
        self.assertTrue('var1' in sergrp.variables)
        self.assertTrue('var2' in sergrp.variables)
        self.assertTrue(sergrp.has_subservice('hpss_nfs'))
        self.assertTrue(sergrp.has_subservice('lustre'))
        self.assertTrue(
            sergrp._subservices['hpss_nfs'].has_parent_dep('sink'))
        self.assertTrue(
            sergrp._subservices['hpss_nfs'].has_child_dep('source'))
        self.assertTrue(
            sergrp._subservices['lustre'].has_parent_dep('sink'))
        self.assertTrue(
            sergrp._subservices['lustre'].has_child_dep('source'))

    def test_fromdict_after(self):
        """Test 'after' as an alias of 'require_weak'"""
        grp = ServiceGroup('grp')
        grp.fromdict({
            'services': {
                'svc1': {
                    'actions': { 'start': { 'cmd': '/bin/true' } }
                },
                'svc2': {
                    'after': [ 'svc1' ],
                    'actions': { 'start': { 'cmd': '/bin/true' } }
                }
            }
        })
        svc1 = grp._subservices['svc2'].parents['svc1']
        self.assertEqual(svc1.dep_type, REQUIRE_WEAK)

    def test_before(self):
        """Test 'before' as an alias of 'after' (only for v1.0 compat)"""
        grp = ServiceGroup('grp')
        grp.fromdict({
            'services': {
                'svc1': {
                    'actions': {'start': {'cmd': '/bin/true'}}
                },
                'svc2': {
                    'before': ['svc1'],
                    'actions': {'start': {'cmd': '/bin/true'}}
                }
            }
        })
        svc1 = grp._subservices['svc2'].parents['svc1']
        self.assertEqual(svc1.dep_type, REQUIRE_WEAK)

    def test_filter(self):
        """Test parsing 'filter' dependency type"""
        grp = ServiceGroup('grp')
        grp.fromdict({
            'services': {
                'svc1': {
                    'actions': {'start': {'cmd': '/bin/true'}}
                },
                'svc2': {
                    'filter': ['svc1'],
                    'actions': {'start': {'cmd': '/bin/true'}}
                }
            }
        })
        svc1 = grp._subservices['svc2'].parents['svc1']
        self.assertEqual(svc1.dep_type, FILTER)

    def test_fromdict2(self):
        '''
        Test instanciation of a service group with dependencies between
        subservices.
        '''
        sergrp = ServiceGroup('S1')
        sergrp.fromdict(
            {'services':
                {'hpss_nfs':
                    {'target': 'localhost',
                     'require': ['lustre', 'test'],
                     'actions':
                        {'start': {'cmd': '/bin/True'},
                        'stop': {'cmd': '/bin/False'}},
                        'desc': "I'm the service hpss_nfs"
                     },
                 'lustre':
                     {'target': 'localhost',
                      'actions':
                        {'start': {'cmd':'/bin/True'},
                         'stop': {'cmd': '/bin/False'}},
                      'desc': "I'm the service lustre"},
                'test':
                     {'target': 'localhost',
                      'actions':
                        {'start': {'cmd':'/bin/True'},
                         'stop': {'cmd': '/bin/False'}},
                      'desc': "I'm a test suite"}},
            'variables':{'LUSTRE_FS_LIST': 'store0,work0'},
            'desc': "I'm the service S1",
            'target': 'localhost',
        })
        self.assertTrue(sergrp.has_subservice('hpss_nfs'))
        self.assertTrue(sergrp.has_subservice('lustre'))
        self.assertTrue(sergrp.has_subservice('test'))
        self.assertFalse(
            sergrp._subservices['hpss_nfs'].has_parent_dep('sink'))
        self.assertTrue(
            sergrp._subservices['hpss_nfs'].has_child_dep('source'))
        self.assertTrue(
            sergrp._subservices['lustre'].has_parent_dep('sink'))
        self.assertFalse(
            sergrp._subservices['test'].has_child_dep('source'))
        self.assertTrue(
            sergrp._subservices['test'].has_parent_dep('sink'))

    def test_require_no_list(self):
        """Test parsing require with a simple singleton (no list)"""
        grp = ServiceGroup('grp')
        grp.fromdict({'services': {
                          'svc1': {
                              'actions': {'start': {'cmd': '/bin/true'}}
                          },
                          'svc2': {
                              'require': 'svc1',
                              'actions': {'start': {'cmd': '/bin/true'}}
                          }
                      }})
        svc1 = grp._subservices['svc2'].parents['svc1']
        self.assertEqual(svc1.dep_type, REQUIRE)

    def test_resolve_all_local_variable(self):
        """Variable resolution in 'require' with a local variable."""
        svcgrp = ServiceGroup('group')
        svcgrp.fromdict({
                        'services': {
                            'dep1': {
                                     'actions': {'start': {'cmd': '/bin/True'}}
                            },
                            'dep2': {
                                     'variables': {'foo': ['dep1']},
                                     'require': "%foo",
                                     'actions': {'start': {'cmd': '/bin/True'}}
                            },
                        }
                        })
        svcgrp.resolve_all()
        service = svcgrp._subservices['dep2']
        self.assertTrue('dep1' in service.deps())

    def test_resolve_all_with_full_config(self):
        """Test instantiation of a service group with variables subservices."""
        sergrp = ServiceGroup('S1')
        sergrp.add_var('TOUT', 1)
        sergrp.add_var('RET', 2)
        sergrp.add_var('FAN', 3)
        sergrp.add_var('DLY', 4)
        sergrp.add_var('ERRS', 0)
        sergrp.add_var('WARN', 5)
        sergrp.add_var('DSC', 'I am the service')
        sergrp.add_var('MD', 'delegate')
        sergrp.add_var('REQUIRES', ["dep1", "dep2"])

        sergrp.fromdict({
                    'desc':   "Check variables",
                    'target': "localhost",
                    'services': {
                        'dep1':
                            {'actions': {'start': {'cmd': '/bin/True'}} },
                        'dep2':
                            {'actions': {'start': {'cmd': '/bin/True'}} },
                        'fullvars': {
                                     'target': 'localhost',
                                     'require': "%REQUIRES",
                                     'timeout': "%TOUT",
                                     'retry': "%RET",
                                     'fanout': "%FAN",
                                     'delay': "%DLY",
                                     'errors': "%ERRS",
                                     'warnings': "%WARN",
                                     'mode': "%MD",
                                     'actions': {
                                                 'start': {'cmd': '/bin/True'},
                                                 'stop':  {'cmd': '/bin/False'}
                                                },
                                     'desc': "%DSC"
                                    }
                         },
                    })
        sergrp.resolve_all()
        service = sergrp._subservices['fullvars']
        self.assertEqual(service.target, NodeSet('localhost'))
        self.assertEqual(service.timeout, 1)
        self.assertEqual(service.maxretry, 2)
        self.assertEqual(service.fanout, 3)
        self.assertEqual(service.delay, 4)
        self.assertEqual(service.errors, 0)
        self.assertEqual(service.warnings, 5)
        self.assertEqual(service.mode, 'delegate')
        self.assertEqual(service.desc, "I am the service")
        self.assertTrue('dep1' in service.deps())
        self.assertTrue('dep2' in service.deps())

    def test_resolve_target_from_parent(self):
        """resolve target using a variable declared in parent service group"""
        # 'target' property is resolved very early and not in resolve_all()
        data = {
            'services': {
                'mygroup': {
                    'variables': {
                        'targets': 'foo',
                    },
                    'services': {
                        'svc': {
                            'target': '%targets',
                            'actions': {'start': {'cmd': '/bin/true'}}
                        }
                    }
                }
            }
        }
        grp = ServiceGroup('grp')
        grp.fromdict(data)
        svc = grp._subservices['mygroup']._subservices['svc']
        self.assertEqual(str(svc.target), 'foo')

    def test_variable_with_escaping_pattern(self):
        """fromdict() should not resolve variables"""
        grp = ServiceGroup('grp')
        grp.fromdict({
            'services': {
                'svc': {
                    'variables': {
                        'foo': 'nice'
                    },
                    'actions': {
                        'start': {'cmd': 'shine config -O %%host %foo'}
                    }
                }
            }
        })
        action = grp._subservices['svc']._actions['start']
        self.assertEqual(action.command, 'shine config -O %%host %foo')

    def test_create_service_imbrications(self):
        '''Test create service with multiple level of subservices'''
        sergrp = ServiceGroup('groupinit')
        sergrp.fromdict(
            {'services':
                {'svcA':
                    {'require': ['subgroup'],
                    'actions':
                        {'start': {'cmd': '/bin/True'},
                        'stop': {'cmd': '/bin/False'}},
                        'desc': 'I am the subservice $NAME'},
                'subgroup':
                    {'services':
                        {'svcB':
                            {'require_weak':['svcC'],
                            'actions':
                                {'start': {'cmd': '/bin/True'},
                            '   stop': {'cmd': '/bin/False'}},
                            'desc': 'I am the subservice $NAME'},
                        'svcC':
                            {'actions':
                                {'start': {'cmd': '/bin/True'},
                                'stop': {'cmd': '/bin/False'}},
                                'desc': 'I am the subservice $NAME'}},
                        'target': '127.0.0.1',
                        'desc': "I'm the service $NAME"}},
            'desc': 'I am a group',
            'target': 'localhost',
        })
        for subservice in ('svcA', 'subgroup'):
            if isinstance(sergrp._subservices[subservice], ServiceGroup):
                for subsubser in ('svcB', 'svcC'):
                    self.assertTrue(
                    sergrp._subservices[subservice].has_subservice(subsubser))
            self.assertTrue(sergrp.has_subservice(subservice))

    def test_inheritance(self):
        '''Test properties inherited from ServiceGroup to Service and Action'''
        sergrp = ServiceGroup('groupinit')
        sergrp.fromdict(
            {'services':
                {'svcA':
                    {'require': ['subgroup'],
                    'actions':
                        {'start': {'cmd': '/bin/True'},
                        'stop': {'cmd': '/bin/False'}},
                        'desc': 'I am the subservice $NAME'},
                'subgroup':
                    {'services':
                        {'svcB':
                            {'require_weak':['svcC'],
                            'actions':
                                {'start': {'cmd': '/bin/True'},
                            '   stop': {'cmd': '/bin/False'}},
                            'desc': 'I am the subservice $NAME'},
                        'svcC':
                            {'actions':
                                {'start': {'cmd': '/bin/True'},
                                'stop': {'cmd': '/bin/False'}},
                                'desc': 'I am the subservice $NAME'}},
                        'target': '127.0.0.1',
                        'desc': "I'm the service $NAME"}},
            'desc': 'I am a group',
            'target': 'localhost',
        })
        self.assertEqual(
            sergrp._subservices['svcA'].target, NodeSet('localhost'))
        self.assertEqual(
            sergrp._subservices['subgroup'].target, NodeSet('127.0.0.1'))
        subgroup = sergrp._subservices['subgroup']
        self.assertEqual(
            subgroup._subservices['svcB'].target, NodeSet('127.0.0.1'))
        self.assertEqual(
            subgroup._subservices['svcC'].target, NodeSet('127.0.0.1'))

    def test_servicegroup_with_nodeset_like_actions_with_one_decl(self):
        '''Test a service group with several group with nodeset-like names'''
        sergrp = ServiceGroup('group1')
        sergrp.fromdict({
            'services': {
                'da[1-3]': {
                    'actions': {'start': {'cmd': '/bin/True'}}
                },
            }})

        self.assertEqual(len(sergrp._subservices), 3)
        self.assertTrue(sergrp.has_subservice('da1'))
        self.assertTrue(sergrp.has_subservice('da2'))
        self.assertTrue(sergrp.has_subservice('da3'))
        self.assertEqual(len(sergrp._subservices['da1']._actions), 1)
        self.assertEqual(len(sergrp._subservices['da2']._actions), 1)
        self.assertEqual(len(sergrp._subservices['da3']._actions), 1)

    def test_subservices_with_different_actions(self):
        '''Test a service group with subservices with different actions'''
        sergrp = ServiceGroup('group1')
        sergrp.fromdict(
            {
            'services': {
                'svc1': {
                    'actions': {
                          'start': {'cmd': '/bin/True'},
                          'status': {'cmd': '/bin/True'},
                          'stop': {'cmd': '/bin/True'},
                    }
                },
                'svc2': {
                    'require': [ 'svc1' ],
                    'actions': {
                          'start': {'cmd': '/bin/True'},
                          'stop': {'cmd': '/bin/True'},
                          'status': {'cmd': '/bin/True'},
                    }
                },
                'svc3': {
                    'require': [ 'svc1' ],
                    'actions': {
                          'start': {'cmd': '/bin/True'},
                          'stop': {'cmd': '/bin/True'},
                          'status': {'cmd': '/bin/True'},
                    }
                },
            }})

        self.assertEqual(len(sergrp._subservices), 3)
        self.assertTrue(sergrp.has_subservice('svc1'))
        self.assertTrue(sergrp.has_subservice('svc2'))
        self.assertTrue(sergrp.has_subservice('svc3'))
        self.assertEqual(len(sergrp._subservices['svc1']._actions), 3)
        self.assertEqual(len(sergrp._subservices['svc2']._actions), 3)
        self.assertEqual(len(sergrp._subservices['svc3']._actions), 3)

    def test_group_with_weak_dep_error(self):
        """A group with a weak dep error runs fine."""

        dep1 = Service('dep1')
        dep1.add_action(Action('stop', command='/bin/false'))

        grp = ServiceGroup('group')
        grp.fromdict({
            'services': {
                'svc1': {
                    'actions': {
                        'stop': { 'cmd': "/bin/true" },
                    }
                }
            }
        })

        grp.add_dep(dep1, sgth=REQUIRE_WEAK)
        grp.run('stop')

        self.assertEqual(grp.status, DONE)

    def test_non_existing_target(self):
        '''Test expected behaviour on an non-existing target'''
        sergrp = ServiceGroup('group1')
        sergrp.fromdict(
                { 'services':
                { 'svc1': {
                    'actions': {
                        'start': {'cmd': '/bin/True'},
                    },
                  'target': '@none',
                }}})
        self.assertEqual(sergrp._subservices['svc1'].target, NodeSet())

    def test_missing_dep_raises_error(self):
        """Require a missing deps raises UnknownDependencyError"""
        grp = ServiceGroup('group')
        self.assertRaises(UnknownDependencyError, grp.fromdict, {
            'services': {
                'svc1': {
                    'require': [ 'bad' ],
                    'actions': {
                        'stop': { 'cmd': "/bin/true" },
                    }
                }
            }
        })

    def test_inter_subservice_deps_multi_level(self):
        '''Test create service with multiple levels of subservices dependencies'''
        sergrp = ServiceGroup('group', root=True)
        sergrp.fromdict({
            'services': {
                'subgroupA': {
                    'services': {
                        'svcA':
                            {'actions':
                                {
                                    'act1': {'cmd': '/bin/true'},
                                },
                                'desc': 'I am the subservice $NAME'
                            },
                        'subsubgrpA': {
                            'services': {
                                'depA': {
                                    #'require': ['subgroupB.svcA'],
                                    'actions':
                                        {
                                            'act1': {'cmd': '/bin/true'},
                                        },
                                    'desc': 'I am the subservice $NAME'
                                },
                            },
                        },
                    },
                },
                'subgroupB': {
                    'services': {
                        'svcA': {
                            'require': ['subgroupA.subsubgrpA.depA'],
                            'actions':
                                {
                                    'act1': {'cmd': '/bin/true'}
                                },
                            'desc': 'I am the subservice $NAME'
                        },
                    },
                },

            },
            'desc': 'I am a first group',
            'target': 'localhost',
        })

        self.assertTrue(sergrp.has_subservice('subgroupA'))
        self.assertTrue(sergrp.has_subservice('subgroupB'))
        self.assertTrue(sergrp._subservices['subgroupA'].has_subservice('subsubgrpA'))
        self.assertTrue(sergrp._subservices['subgroupA']._subservices['subsubgrpA'].has_subservice('depA'))
        self.assertTrue(sergrp._subservices['subgroupA'].has_subservice('svcA'))
        self.assertTrue(sergrp._subservices['subgroupB'].has_subservice('svcA'))

        sergrp.run('act1')
        self.assertEqual(sergrp.status, DONE)

    def test_inter_subservice_deps_dict(self):
        '''Test create service with multiple level of subservices dependencies'''
        sergrp = ServiceGroup('group', root=True)
        sergrp.fromdict(
            {'services': {
                'subgroupA': {
                    'services': {
                        'svcA':
                            {'actions':
                                {
                                    'act1,act2': {'cmd': '/bin/true'},
                                },
                                'desc': 'I am the subservice $NAME'
                            },
                        'svcB':
                            {'require': ['svcA'],
                             'actions':
                                 {
                                     'act1': {'cmd': '/bin/true'},
                                     'act2': {'cmd': '/bin/false'},
                                 },
                             'desc': 'I am the subservice $NAME'
                             }
                    }
                },
                'subgroupB': {
                    'services': {
                        'svcA': {
                            'require': ['subgroupA.svcB'],
                            'actions':
                                {
                                    'act1,act2': {'cmd': '/bin/true'}
                                },
                            'desc': 'I am the subservice $NAME'
                        },
                        'svcB': {
                            'actions':
                                {
                                    'act1,act2': {'cmd': '/bin/true'}
                                },
                            'desc': 'I am the subservice $NAME'
                        }
                    }
                }

                },
            'desc': 'I am a first group',
            'target': 'localhost',
        })

        self.assertTrue(sergrp.has_subservice('subgroupA'))
        self.assertTrue(sergrp.has_subservice('subgroupB'))
        for subservice in ('svcA', 'svcB'):
            self.assertTrue(sergrp._subservices['subgroupA'].has_subservice(subservice))
            self.assertTrue(sergrp._subservices['subgroupB'].has_subservice(subservice))


        sergrp.run('act1')
        self.assertEqual(sergrp.status, DONE)
        sergrp.reset()
        sergrp.run('act2')
        self.assertEqual(sergrp.status, DEP_ERROR)

    def test_inter_subservice_deps_dict_unknown_dep(self):
        '''Test create service with multiple level of subservices dependencies'''
        sergrp = ServiceGroup('group')
        self.assertRaises(UnknownDependencyError, sergrp.fromdict, {
            'services': {
                'subgroupA': {
                    'services': {
                        'svcA':
                            {'actions':
                                {
                                    'act1,act2': {'cmd': '/bin/true'},
                                },
                                'desc': 'I am the subservice $NAME'
                            },
                        'svcB':
                            {'require': ['svcA'],
                             'actions':
                                 {
                                     'act1': {'cmd': '/bin/true'},
                                     'act2': {'cmd': '/bin/false'},
                                 },
                             'desc': 'I am the subservice $NAME'
                             }
                    }
                },
                'subgroupB': {
                    'services': {
                        'svcA': {
                            'require': ['subgroupA.svcB'],
                            'actions':
                                {
                                    'act1,act2': {'cmd': '/bin/true'}
                                },
                            'desc': 'I am the subservice $NAME'
                        },
                        'svcB': {
                            'actions':
                                {
                                    'act1,act2': {'cmd': '/bin/true'}
                                },
                            'desc': 'I am the subservice $NAME'
                        }
                    }
                }

            },
            'desc': 'I am a first group',
            'target': 'localhost',
        })

    def test_inter_subservice_deps_dict_nested(self):
        '''Test create service with multiple level of subservices dependencies'''
        sergrp = ServiceGroup('group', root=True)
        sergrp.fromdict(
            {'services': {
                'subgroupA': {
                    'services': {
                        'svcA':
                            {'actions':
                                {
                                    'act1,act2': {'cmd': '/bin/true'},
                                },
                                'desc': 'I am the subservice $NAME'
                            },
                        'svcB':
                            {'require': ['svcA'],
                             'services': {
                                 'subsvc': {
                                     'actions':{
                                         'act1': {'cmd': '/bin/true'},
                                         'act2': {'cmd': '/bin/false'},
                                     }
                                 }
                             },
                             'desc': 'I am the subservice $NAME'
                             }
                    }
                },
                'subgroupB': {
                    'services': {
                        'svcA': {
                            'require': ['svcB.subsvc'],
                            'actions':
                                {
                                    'act1,act2': {'cmd': '/bin/true'}
                                },
                            'desc': 'I am the subservice $NAME'
                        },
                        'svcB': {
                            'actions':
                                {
                                    'act1,act2': {'cmd': '/bin/true'}
                                },
                            'desc': 'I am the subservice $NAME'
                        }
                    }
                }

                },
            'desc': 'I am a first group',
            'target': 'localhost',
        })

        self.assertTrue(sergrp.has_subservice('subgroupA'))
        self.assertTrue(sergrp.has_subservice('subgroupB'))
        for subservice in ('svcA', 'svcB'):
            self.assertTrue(sergrp._subservices['subgroupA'].has_subservice(subservice))
            self.assertTrue(sergrp._subservices['subgroupB'].has_subservice(subservice))


        sergrp.run('act1')
        self.assertEqual(sergrp.status, DONE)
        sergrp.reset()
        sergrp.run('act2')
        self.assertEqual(sergrp.status, DEP_ERROR)
