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
        # Entity name
        self.name = name
        # Entity description
        self.description = None
        # Maximum window for parallelism
        self.fanout = None
        # Nodes on which the entity is launched
        self.target = target
        # Maximum error authorized per entity
        self.errors = 0
        # Parent entity
        self.parent = None
        # Entity childs
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