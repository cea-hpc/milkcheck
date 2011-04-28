# Copyright CEA (2011)  
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This module contains the BaseEntity class definition
"""

# Classes
from MilkCheck.Engine.Dependency import Dependency

# Symbols
from MilkCheck.Engine.Dependency import CHECK, REQUIRE, REQUIRE_WEAK

# Status available for an entity

# Typically this means that the entity has no status (not any process done) 
NO_STATUS = "NO_STATUS"

# This entity is doing something which is not done yet
WAITING_STATUS = "WAITING_STATUS"

# Compute starting by the entity is done
RUNNING = "RUNNING"

# Compute starting by the entity is done but it encountered some issues
RUNNING_WITH_WARNINGS = "SUCCESS_WITH_WARNINGS"

# Time allowed for the entity to perform a task is over whereas the task
# itself is not done
TIMED_OUT = "TIMED_OUT"

# Error limit is overrun for the task performed by the entity 
TOO_MANY_ERRORS = "TOO_MANY_ERRORS"

# Specified that the entity has an error
ERROR = "ERROR"



class MilkCheckEngineError(Exception):
    """Base class for Engine exceptions."""

class DependencyAlreadyReferenced(MilkCheckEngineError):
    """
    This exception is raised if you try to add two times the same
    depedency to the same service.
    """
class IllegalDependencyTypeError(MilkCheckEngineError):
    """
    Exception raised when you try to assign another identifier than
    CHECK, REQUIRE OR REQUIRE_WEAK to dep_type
    """

class BaseEntity(object):
    """
    Base class which models the attributes common between Action and
    BaseService. This class is abstract and shall not be instanciated.
    """
    def __init__(self, name, target=None):
        # Entity name
        self.name = name
        
        # Define the initial status
        self.status = NO_STATUS
        
        # Entity description
        self.desc = None
        
        # Maximum window for parallelism
        self.fanout = None
        
        # Nodes on which the entity is launched
        self.target = target
        
        # Maximum error authorized per entity
        self.errors = 0
        
        # Parents dependencies (e.g A->B so B is the parent of A)
        self.parents = {}
        
        # Children dependencies (e.g A<-B) so A is a child of B)
        self.children = {}
    
    def add_dep(self, target, sgth=REQUIRE, parent=True, inter=False):
        """
        Add a dependency either in parents or children dictionnary. This allow
        you to specify the strenght of the dependency and if the dependency is
        internal.
        """
        assert target, "target must not be None"
        if sgth in (CHECK, REQUIRE, REQUIRE_WEAK):
            if parent:
                if target.name in self.parents:
                    raise DependencyAlreadyReferenced()
                else:
                    # This dependency is considered as a parent of the
                    # current object
                    self.parents[target.name] = Dependency(target, sgth, inter)
                    target.children[self.name] = Dependency(self, sgth, inter)
            else:
                if target.name in self.children:
                    raise DependencyAlreadyReferenced()
                else:
                    # This dependency is considered as a child of the
                    # current object
                    self.children[target.name] = Dependency(target, sgth, inter)
                    target.parents[self.name] = Dependency(self, sgth, inter)
        else:
            raise IllegalDependencyTypeError
            
    def remove_dep(self, dep_name, parent=True):
        """
        Remove a dependency on both side, in the current object and in the
        target object concerned by the dependency
        """
        assert dep_name, "Dependency specified must not be None"
        if parent and dep_name in self.parents:
            dep = self.parents[dep_name]
            del self.parents[dep_name]
            del dep.target.children[self.name]
        elif dep_name in self.children:
            dep = self.children[dep_name]
            del self.children[dep_name]
            del dep.target.parents[self.name]
            
    def has_child_dep(self, dep_name):
        """
        Determine whether the current object has a child dependency called
        dep_name
        """
        return dep_name in self.children
        
    def has_parent_dep(self, dep_name):
        """
        Determine whether the current object has a parent dependency called
        dep_name
        """
        return dep_name in self.parents
        
    def clear_deps(self):
        """Clear parent/child dependencies."""
        self.parents.clear()
        self.children.clear()
        
    def has_waiting_deps(self, reverse=False):
        """
        Allow us to determine if the current services has to wait before to
        start due to unterminated dependencies.
        """
        deps = self.parents
        if reverse:
            deps = self.children
        for dep_name in deps:
            if deps[dep_name].target.status == WAITING_STATUS:
                return True
        return False

        
    def search_deps(self, symbols=None, reverse=False):
        """
        Look for parent/child dependencies matching to the symbols. The
        search direction depends on the reverse flag's value
        """
        matching = []
        deps = self.parents
        if reverse:
            deps = self.children  
        for dep_name in deps:
            if symbols and deps[dep_name].target.status in symbols:
                matching.append(deps[dep_name])
            elif not symbols:
                matching.append(deps[dep_name])
        return matching
        
    def eval_deps_status(self, reverse=False):
        """
        Evaluate the status of parent/child dependencies depending
        on the value of the reverse flag
        """
        raise NotImplementedError