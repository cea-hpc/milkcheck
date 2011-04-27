# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
Test cases for the BaseEntity classes.
"""

import unittest

from MilkCheck.Engine.BaseEntity import BaseEntity


class BaseEntityTest(unittest.TestCase):
    """Tests cases for the class BaseEntity."""
    def test_instanciation_base_entity(self):
        """Test BaseEntity object instanciation."""
        ent = BaseEntity('foo')
        self.assertTrue(ent)
        self.assertTrue(isinstance(ent, BaseEntity))
        self.assertEqual(ent.name, 'foo')
        ent = BaseEntity(name='foo', target='fortoy5')
        self.assertEqual(ent.target, 'fortoy5')

    def test_has_child(self):
        """Test method has_child."""
        ent = BaseEntity('foo')
        child = BaseEntity('child')
        ent.children.append(child)
        self.assertTrue(ent.has_child(child))
        ent.children.remove(child)
        self.assertFalse(ent.has_child(child))

    def test_add_child(self):
        """Test method add_child behaviour."""
        ent = BaseEntity('foo')
        child = BaseEntity('child')
        ent.add_child(child)
        self.assertTrue(ent.has_child(child))
        self.assertRaises(ValueError, ent.add_child, None)

    def test_remove_child(self):
        """Test method remove_child behaviour."""
        ent = BaseEntity('foo')
        child = BaseEntity('child')
        ent.add_child(child)
        ent.remove_child(child)
        self.assertFalse(ent.has_child(child))
        self.assertRaises(ValueError, ent.remove_child, child)
        self.assertRaises(ValueError, ent.remove_child, None)