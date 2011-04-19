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

# Exceptions
from MilkCheck.Engine.ServiceGroup import ServiceAlreadyReferencedError
from MilkCheck.Engine.ServiceGroup import ServiceNotFoundError

# Symbols
from MilkCheck.Engine.BaseService import SUCCESS, NO_STATUS

class ServiceGroupTest(TestCase):
    """Define the test cases of a ServiceGroup."""
    
    def test_instanciation_service_group(self):
        """Test instanciation of a ServiceGroup"""
        ser_group = ServiceGroup("GROUP")
        self.assertTrue(ser_group)
        self.assertTrue(isinstance(ser_group, ServiceGroup))
        self.assertEqual(ser_group.name, "GROUP")
        
    def test_search_deps(self):
        """Test the method search deps overriden from BaseService"""
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
        """Test method prepare with an single empty ServiceGroup"""
        group = ServiceGroup("GROUP")
        group.prepare("start")
        self.assertEqual(group.status, SUCCESS)
        
    def test_prepare_group_subservice(self):
        """Test prepare group with an internal dependency"""
        group = ServiceGroup("GROUP")
        subserv = Service("SUB1")
        subserv.add_action(Action("start", "localhost", "/bin/true"))
        group.add_dependency(service=subserv, internal=True)
        group.prepare("start")
        group.resume()
        self.assertEqual(group.status, SUCCESS)
        self.assertEqual(subserv.status, SUCCESS)
        
    def test_prepare_group_subservices(self):
        """Test prepare group with multiple internal dependencies"""
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