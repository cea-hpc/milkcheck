#coding=utf-8
#copyright CEA (2011)  
#contributor: TATIBOUET Jérémie <tatibouetj@ocre.cea.fr>

"""
This module contains the BaseEntity class definition
"""


class BaseEntity(object):
    
    """Base class which models the attributes
       common between Action and BaseService.
       This class is abstract and shall no be instantiated"""
       
    def __init__(self, name):
        self.name = name
        self.description = None
        self.fanout = None
        self.target = None
        self.errors = 0
        self.children = []
   
    def remove_child(self, child):
        """Remove the specified child from children"""
        self.children.remove(child)
    
    def add_child(self, child):
        """Add a child to the children list"""
        self.children.append(child)