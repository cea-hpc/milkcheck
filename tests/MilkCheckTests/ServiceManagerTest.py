# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This modules defines the tests cases targeting the internal class
RunningTasksManager and the ServiceManager itself
"""

# Classes
from unittest import TestCase
from MilkCheck.Engine.Action import Action
from MilkCheck.ServiceManager import ServiceManager, service_manager_self


class ServiceManagerTest(TestCase):
    """Tests cases for the class ServiceManager"""
    
    def test_instanciation(self):
        """Test the instanciation of the singleton class ServiceManager"""
        manager = service_manager_self()
        same_manager = service_manager_self()
        self.assertTrue(manager is same_manager)