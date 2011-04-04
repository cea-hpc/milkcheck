# coding=utf-8
# Copyright CEA (2011) 
# Contributor: TATIBOUET Jérémie <tatibouetj@ocre.cea.fr>

"""
This modules defines the tests cases targeting the Action and Service objects
"""
import sys
from exceptions import TypeError
from unittest import TestCase

from MilkCheck.Engine.Service import Service
from MilkCheck.Engine.Action import Action

class ActionTest(TestCase):
    """
    Define the unit tests for the object action
    """
    def setUp(self):
        self._action = None
    
    def test_action_instanciation(self):
        """Check instanciation of an action"""
        self._action = Action("start")
        self.assertNotEqual(self._action, None, "should be none")
        self.assertEqual(self._action.name, "start", "wrong name")
        
class ServiceTest(TestCase):
   
    """
    Define the unit tests for the object service
    """
   
    def setUp(self):
        self._service = None
   
    def test_service_instanciation(self):
        """
        Check instanciation of a service
        """
        self._service = Service("brutus")
        self.assertNotEqual(self._service, None, "should be none")
        self.assertEqual(self._service.name, "brutus", "wrong name")
        
    def test_add_action(self):
        """
        Check add_action_behaviour
        """