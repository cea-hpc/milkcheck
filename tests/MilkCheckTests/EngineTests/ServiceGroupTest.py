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

# Symbols
from MilkCheck.Engine.BaseService import DONE, NO_STATUS
from MilkCheck.Engine.BaseService import TOO_MANY_ERRORS, ERROR
from MilkCheck.Engine.BaseService import DONE_WITH_WARNINGS
from MilkCheck.Engine.Dependency import CHECK, REQUIRE_WEAK

class ServiceGroupTest(TestCase):
    '''Define the test cases of a ServiceGroup.'''
    
    def test_instanciation_service_group(self):
        '''Test instanciation of a ServiceGroup.'''
        ser_group = ServiceGroup('GROUP')
        self.assertTrue(ser_group)
        self.assertTrue(isinstance(ser_group, ServiceGroup))
        self.assertEqual(ser_group.name, 'GROUP')
    
    def test_has_subservice(self):
        '''Test whether a service is an internal dependency of a group'''
        group = ServiceGroup('group')
        serv = Service('intern_service')
        self.assertFalse(group.has_subservice(serv.name))
        group.add_dep(target=serv, inter=True)
        self.assertTrue(group.has_subservice(serv.name))
        
    def test_search_deps(self):
        '''Test the method search deps overriden from BaseService.'''
        group = ServiceGroup('GROUP')
        serv = Service('SERVICE')
        group_dep =  ServiceGroup('GROUP2')
        group.add_dep(target=serv, inter=True)
        group.add_dep(group_dep)
        deps = group.search_deps([NO_STATUS])
        self.assertEqual(len(deps['external']), 1)
        self.assertEqual(len(deps['internal']), 1)
        serva = Service('A')
        serva.status = DONE
        group.add_dep(serva)
        deps = group.search_deps([NO_STATUS, DONE])
        self.assertEqual(len(deps['external']), 2)
       
    def test_prepare_empty_group(self):
        '''Test method prepare with a single empty ServiceGroup.'''
        group = ServiceGroup('GROUP')
        group.prepare('start')
        self.assertEqual(group.status, DONE)
        
    def test_prepare_group_subservice(self):
        '''Test prepare group with an internal dependency.'''
        group = ServiceGroup('GROUP')
        subserv = Service('SUB1')
        subserv.add_action(Action('start', 'localhost', '/bin/true'))
        group.add_dep(target=subserv, inter=True)
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
        
        subserv_a.add_dep(subserv_c)
        subserv_b.add_dep(subserv_c)
        group.add_dep(target=subserv_a, inter=True)
        group.add_dep(target=subserv_b, inter=True)
        
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
        group.add_dep(target=inter_serv1, inter=True)
        group.add_dep(target=inter_serv2, inter=True)
        inter_serv2.add_dep(inter_serv3)
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
        
    def test_prepare_group_with_errors(self):
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
        ac_err2 = Action('status', 'localhost', '/bin/false')
        # Add actions
        inter_serv1.add_action(ac_suc1)
        inter_serv2.add_action(ac_suc2)
        inter_serv3.add_action(ac_err1)
        ext_serv1.add_action(ac_suc3)
        ext_serv2.add_action(ac_err2)
        # Add dependencies
        group.add_dep(target=inter_serv1, inter=True)
        group.add_dep(target=inter_serv2, inter=True)
        inter_serv2.add_dep(inter_serv3, dtype=REQUIRE_WEAK)
        group.add_dep(ext_serv1)
        group.add_dep(service=ext_serv2, dtype=REQUIRE_WEAK)
        # Prepare group
        group.run('start')
        self.assertEqual(group.status, DONE_WITH_WARNINGS)
        self.assertEqual(ext_serv1.status, DONE)
        self.assertEqual(ext_serv2.status, TOO_MANY_ERRORS)
        self.assertEqual(inter_serv1.status, DONE)
        self.assertEqual(inter_serv2.status, DONE_WITH_WARNINGS)
        self.assertEqual(inter_serv3.status, TOO_MANY_ERRORS)
        
    def test_prepare_group_with_errors(self):
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
        group.add_dep(target=inter_serv1, inter=True)
        group.add_dep(target=inter_serv2, inter=True)
        inter_serv2.add_dep(target=inter_serv3, sgth=CHECK)
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
        serv_a.add_dep(target=serv_c, inter=True)
        serv_a.run('start')
        self.assertEqual(serv.status, NO_STATUS)
        self.assertEqual(serv_a.status, DONE)
        self.assertEqual(serv_b.status, DONE)
        self.assertEqual(serv_c.status, DONE)