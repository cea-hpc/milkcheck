# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This modules defines the tests cases targeting the ServiceGroup object
"""

import sys
from unittest import TestCase

# Classes
from MilkCheck.Engine.ServiceGroup import ServiceGroup
from MilkCheck.Engine.Service import Service
from MilkCheck.Engine.Action import Action

# Symbols
from MilkCheck.Engine.BaseService import SUCCESS, NO_STATUS
from MilkCheck.Engine.BaseService import TOO_MANY_ERRORS, ERROR
from MilkCheck.Engine.BaseService import SUCCESS_WITH_WARNINGS
from MilkCheck.Engine.Dependency import CHECK, REQUIRE_WEAK

class ServiceGroupTest(TestCase):
    """Define the test cases of a ServiceGroup."""
    
    def test_instanciation_service_group(self):
        """Test instanciation of a ServiceGroup."""
        ser_group = ServiceGroup("GROUP")
        self.assertTrue(ser_group)
        self.assertTrue(isinstance(ser_group, ServiceGroup))
        self.assertEqual(ser_group.name, "GROUP")
    
    def test_has_subservice(self):
        """Test whether a service is an internal dependency of a group""" 
        group = ServiceGroup("group")
        serv = Service("intern_service")
        self.assertFalse(group.has_subservice(serv.name))
        group.add_dependency(service=serv, internal=True)
        self.assertTrue(group.has_subservice(serv.name))
        
    def test_search_deps(self):
        """Test the method search deps overriden from BaseService."""
        group = ServiceGroup("GROUP")
        serv = Service("SERVICE")
        group_dep =  ServiceGroup("GROUP2")
        group.add_dependency(service=serv, internal=True)
        group.add_dependency(group_dep)
        deps = group.search_deps([NO_STATUS])
        self.assertEqual(len(deps["external"]),1)
        self.assertEqual(len(deps["internal"]),1)
        serva = Service("A")
        serva.status = SUCCESS
        group.add_dependency(serva)
        deps = group.search_deps([NO_STATUS, SUCCESS])
        self.assertEqual(len(deps["external"]),2)
       
    def test_prepare_empty_group(self):
        """Test method prepare with a single empty ServiceGroup."""
        group = ServiceGroup("GROUP")
        group.prepare("start")
        self.assertEqual(group.status, SUCCESS)
        
    def test_prepare_group_subservice(self):
        """Test prepare group with an internal dependency."""
        group = ServiceGroup("GROUP")
        subserv = Service("SUB1")
        subserv.add_action(Action("start", "localhost", "/bin/true"))
        group.add_dependency(service=subserv, internal=True)
        group.prepare("start")
        group.resume()
        self.assertEqual(group.status, SUCCESS)
        self.assertEqual(subserv.status, SUCCESS)
        
    def test_prepare_group_subservices(self):
        """Test prepare group with multiple internal dependencies."""
        group = ServiceGroup("GROUP")
        ac_suc = Action("start", "localhost", "/bin/true")
        
        subserv_a = Service("SUB1")
        subserv_b = Service("SUB2")
        subserv_c = Service("SUB3")
        
        subserv_a.add_action(ac_suc)
        subserv_b.add_action(ac_suc)
        subserv_c.add_action(ac_suc)
        
        subserv_a.add_dependency(subserv_c)
        subserv_b.add_dependency(subserv_c)
        group.add_dependency(service=subserv_a, internal=True)
        group.add_dependency(service=subserv_b, internal=True)
        
        group.prepare("start")
        group.resume()
        self.assertEqual(group.status, SUCCESS)
        self.assertEqual(subserv_a.status, SUCCESS)
        self.assertEqual(subserv_b.status, SUCCESS)
        self.assertEqual(subserv_c.status, SUCCESS)
     
    def test_prepare_empty_group_external_deps(self):
        """Test prepare an empty group with a single external dependency."""
        group = ServiceGroup("GROUP")
        ext_serv = Service("EXT_SERV")
        ac_suc = Action("start", "localhost", "/bin/true")
        ext_serv.add_action(ac_suc)
        group.add_dependency(ext_serv)
        group.prepare("start")
        group.resume()
        self.assertEqual(group.status, SUCCESS)
        self.assertEqual(ext_serv.status, SUCCESS)
        
    def test_prepare_group_internal_external_deps(self):
        """Test prepare a group with internal and external dependencies"""
        # Group
        group = ServiceGroup("GROUP")
        # Internal
        inter_serv1 = Service("INT_SERV1") 
        inter_serv2 = Service("INT_SERV2")
        inter_serv3 = Service("INT_SERV3")
        # External
        ext_serv1 =  Service("EXT_SERV1")
        ext_serv2 = Service("EXT_SERV2")
        ac_suc = Action("start", "localhost", "/bin/true")
        # Add actions
        inter_serv1.add_action(ac_suc)
        inter_serv2.add_action(ac_suc)
        inter_serv3.add_action(ac_suc)
        ext_serv1.add_action(ac_suc)
        ext_serv2.add_action(ac_suc)
        # Add dependencies
        group.add_dependency(service=inter_serv1, internal=True)
        group.add_dependency(service=inter_serv2, internal=True)
        inter_serv2.add_dependency(inter_serv3)
        group.add_dependency(ext_serv1)
        group.add_dependency(ext_serv2)
        # Prepare group
        group.prepare("start")
        group.resume()
        self.assertEqual(group.status, SUCCESS)
        self.assertEqual(ext_serv1.status, SUCCESS)
        self.assertEqual(ext_serv2.status, SUCCESS)
        self.assertEqual(inter_serv1.status, SUCCESS)
        self.assertEqual(inter_serv2.status, SUCCESS)
        self.assertEqual(inter_serv3.status, SUCCESS)
        
    def test_prepare_group_with_errors(self):
        """Test prepare a group terminated by SUCCESS_WITH_WARNINGS"""
        # Group
        group = ServiceGroup("GROUP")
        # Internal
        inter_serv1 = Service("INT_SERV1") 
        inter_serv2 = Service("INT_SERV2")
        inter_serv3 = Service("INT_SERV3")
        # External
        ext_serv1 =  Service("EXT_SERV1")
        ext_serv2 = Service("EXT_SERV2")
        ac_suc = Action("start", "localhost", "/bin/true")
        ac_err = Action("start", "localhost", "/bin/false")
        ac_err_chk = Action("status", "localhost", "/bin/false")
        # Add actions
        inter_serv1.add_action(ac_suc)
        inter_serv2.add_action(ac_suc)
        inter_serv3.add_action(ac_err)
        ext_serv1.add_action(ac_suc)
        ext_serv2.add_action(ac_err)
        # Add dependencies
        group.add_dependency(service=inter_serv1, internal=True)
        group.add_dependency(service=inter_serv2, internal=True)
        inter_serv2.add_dependency(inter_serv3, dep_type=REQUIRE_WEAK)
        group.add_dependency(ext_serv1)
        group.add_dependency(service=ext_serv2, dep_type=REQUIRE_WEAK)
        # Prepare group
        group.prepare("start")
        group.resume()
        self.assertEqual(group.status, SUCCESS_WITH_WARNINGS)
        self.assertEqual(ext_serv1.status, SUCCESS)
        self.assertEqual(ext_serv2.status, TOO_MANY_ERRORS)
        self.assertEqual(inter_serv1.status, SUCCESS)
        self.assertEqual(inter_serv2.status, SUCCESS_WITH_WARNINGS)
        self.assertEqual(inter_serv3.status, TOO_MANY_ERRORS)
        
    def test_prepare_group_with_errors(self):
        """Test prepare a group terminated by ERROR"""
        # Group
        group = ServiceGroup("GROUP")
        # Internal
        inter_serv1 = Service("INT_SERV1") 
        inter_serv2 = Service("INT_SERV2")
        inter_serv3 = Service("INT_SERV3")
        # External
        ext_serv1 =  Service("EXT_SERV1")
        ext_serv2 = Service("EXT_SERV2")
        ac_suc = Action("start", "localhost", "/bin/true")
        ac_err = Action("start", "localhost", "/bin/false")
        ac_err_chk = Action("status", "localhost", "/bin/false")
        # Add actions
        inter_serv1.add_action(ac_suc)
        inter_serv2.add_action(ac_suc)
        inter_serv3.add_action(ac_err_chk)
        ext_serv1.add_action(ac_suc)
        ext_serv2.add_action(ac_err)
        # Add dependencies
        group.add_dependency(service=inter_serv1, internal=True)
        group.add_dependency(service=inter_serv2, internal=True)
        inter_serv2.add_dependency(inter_serv3, dep_type=CHECK)
        group.add_dependency(ext_serv1)
        group.add_dependency(service=ext_serv2, dep_type=REQUIRE_WEAK)
        # Prepare group
        group.prepare("start")
        group.resume()
        self.assertEqual(group.status, ERROR)
        self.assertEqual(ext_serv1.status, SUCCESS)
        self.assertEqual(ext_serv2.status, TOO_MANY_ERRORS)
        self.assertEqual(inter_serv1.status, SUCCESS)
        self.assertEqual(inter_serv2.status, ERROR)
        self.assertEqual(inter_serv3.status, TOO_MANY_ERRORS)
        
    def test_run_partial_deps(self):
        """Test stop algorithm as soon as the calling point is done."""
        serv = Service("NOT_CALLED")
        serv_a = ServiceGroup("CALLING_GROUP")
        serv_b = Service("SERV_1")
        serv_c = Service("SERV_2")
        act_suc = Action("start", "localhost", "/bin/true")
        serv_b.add_action(act_suc)
        serv_c.add_action(act_suc)
        serv.add_dependency(serv_a)
        serv_a.add_dependency(service=serv_b)
        serv_a.add_dependency(service=serv_c, internal=True)
        serv_a.run("start")
        self.assertEqual(serv.status, NO_STATUS)
        self.assertEqual(serv_a.status, SUCCESS)
        self.assertEqual(serv_b.status, SUCCESS)
        self.assertEqual(serv_c.status, SUCCESS)