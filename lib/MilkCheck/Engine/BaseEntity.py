# Copyright CEA (2011)  
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This module contains the BaseEntity class definition
"""

        
class MilkCheckEngineError(Exception):
    """Base class for Engine exceptions."""

class BaseEntity(object):
    """
    Base class which models the attributes common between Action and
    BaseService. This class is abstract and shall not be instanciated.
    """
    def __init__(self, name, target=None):
        self.name = name
        self.description = None
        self.fanout = None
        self.target = target
        self.errors = 0
        self.children = []
   
    def remove_child(self, child):
        """Remove the specified child from children."""
        self.children.remove(child)
    
    def add_child(self, child):
        """Add a child to the children list."""
        if not child:
            raise ValueError
        self.children.append(child)
        
    def has_child(self, child):
        """Check is a child is registred."""
        return child in self.children