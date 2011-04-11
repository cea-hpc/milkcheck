# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This modules defines the tests cases targeting the Action and Service objects
"""

import sys
from unittest import TestCase
from MilkCheck.Engine.Service import Service
from MilkCheck.Engine.Action import Action

class ActionTest(TestCase):
    """
    Define the unit tests for the object action
    """
    def test_action_instanciation(self):
        """Check instanciation of an action"""
        action = Action("start")
        self.assertNotEqual(action, None, "should be none")
        self.assertEqual(action.name, "start", "wrong name")
        
class ServiceTest(TestCase):
    """
    Define the unit tests for the object service
    """
    def test_service_instanciation(self):
        """
        Check instanciation of a service
        """
        service = Service("brutus")
        self.assertNotEqual(service, None, "should be none")
        self.assertEqual(service.name, "brutus", "wrong name")
        
    def test_add_action(self):
        """
        Check add_action_behaviour
        """