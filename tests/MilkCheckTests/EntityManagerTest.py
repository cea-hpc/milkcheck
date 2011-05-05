# Copyright CEA (2011)
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This modules defines the tests cases targeting the class
entity manager
"""

# Classes
from unittest import TestCase
from MilkCheck.EntityManager import entity_manager_self
from MilkCheck.Engine.BaseEntity import BaseEntity

class EntityManagerTest(TestCase):
    """Test cases for EntityManager"""

    def test_instanciation(self):
        """test on the instanciation of a manager"""
        manager = entity_manager_self()
        manager.entities['foo'] = BaseEntity('foo')
        same_manager = entity_manager_self()
        self.assertTrue(manager is same_manager)
        self.assertEqual(len(same_manager.entities), 1)

    def test_reverse_mod(self):
        """Test enable reverse mod over a bunch of entity"""
        ent1 = BaseEntity('foo')
        ent2 = BaseEntity('bar')
        manager = entity_manager_self()
        manager.entities['foo'] = ent1
        manager.entities['bar'] = ent2
        self.assertRaises(AssertionError, manager._reverse_mod, None)
        manager._reverse_mod(True)
        self.assertTrue(ent1.algo_dir and ent2.algo_dir)
        self.assertFalse(not ent1.algo_dir and not ent2.algo_dir)