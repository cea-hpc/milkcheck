# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This modules defines the tests cases targeting the BaseService
"""
from unittest import TestCase

# Classes
from MilkCheck.Engine.BaseService import BaseService

# Symbols
from MilkCheck.Engine.BaseService import DONE

class BaseServiceTest(TestCase):
    """
    Test cases for the class BaseService
    """
        
    def test_update_status(self):
        """Test the method update_status without children."""
        serv_a = BaseService("HIGHER_POINT")
        serv_b = BaseService("LEFT_POINT")
        serv_c = BaseService("RIGHT_POINT")
        serv_b.add_dep(serv_a)
        serv_c.add_dep(serv_a)
        self.assertRaises(NotImplementedError, serv_a.update_status, DONE)
        
    def test_run(self):
        """Test the method run"""
        serv_a = BaseService("HIGHER_POINT")
        self.assertRaises(NotImplementedError, serv_a.run, 'fake')
        self.assertTrue(serv_a.origin)