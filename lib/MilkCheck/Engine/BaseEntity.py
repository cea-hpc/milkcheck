# Copyright CEA (2011)  
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This module contains the BaseEntity class definition
"""

# Classes
from ClusterShell.NodeSet import NodeSet
from MilkCheck.Engine.Dependency import Dependency

# Symbols
from MilkCheck.Engine.Dependency import CHECK, REQUIRE, REQUIRE_WEAK

# Status available for an entity

# Typically this means that the entity has no status (not any process done) 
NO_STATUS = 'NO_STATUS'

# This entity is doing something which is not done yet
WAITING_STATUS = 'WAITING_STATUS'

# Compute starting by the entity is done
DONE = 'DONE'

# Compute starting by the entity is done but it encountered some issues
DONE_WITH_WARNINGS = 'DONE_WITH_WARNINGS'

# Time allowed for the entity to perform a task is over whereas the task
# itself is not done
TIMED_OUT = 'TIMED_OUT'

# Error limit is overrun for the task performed by the entity 
TOO_MANY_ERRORS = 'TOO MANY ERRORS'

# Specify that the entity has an error
ERROR = 'ERROR'

# Specify that the entities is locked. An entity which is clocked
# cannot be processed by the engine.
LOCKED = 'LOCKED'

class MilkCheckEngineError(Exception):
    """Base class for Engine exceptions."""

class DependencyAlreadyReferenced(MilkCheckEngineError):
    """
    This exception is raised if you try to add two times the same
    depedency to the same entity.
    """
class IllegalDependencyTypeError(MilkCheckEngineError):
    """
    Exception raised when you try to assign another identifier than
    CHECK, REQUIRE OR REQUIRE_WEAK to dep_type
    """

class BaseEntity(object):
    '''
    This class is abstract and shall not be instanciated.
    A BaseEntity object basically represents a node of graph with reference
    on parents and children.
    '''
    def __init__(self, name, target=None):
        # Entity name
        self.name = name
        
        # Each entity has a status which it state
        self.status = NO_STATUS
        
        # Description of an entity
        self.desc = None
        
        # Maximum window for parallelism. A None fanout means
        # that the task will be limited by the default value of
        # ClusterShell 64
        self.fanout = None
        
        # Nodes on which the entity is launched
        self.target = target
        self._target = self.target
        self._target_backup = self.target
        
        # Maximum error authorized for the entity
        self.errors = 0
        
        # Parents dependencies (e.g A->B so B is the parent of A)
        self.parents = {}
        
        # Children dependencies (e.g A<-B) so A is a child of B)
        self.children = {}

        # Agorithm's direction used
        # False : go in parent's direction
        # True : go in children direction
        self._algo_reversed = False

        # Tag the entity. By this way we know if the entity have to be
        # call by her dependencies
        self._tagged = False

    def update_target(self, nodeset, mode=None):
        '''Update the attribute target of an entity'''
        assert nodeset, 'The nodeset cannot be None'
        if not mode:
            self.target = nodeset
        elif mode is 'DIF':
            self.target.difference_update(nodeset)
        elif mode is 'INT':
            self.target.intersection_update(nodeset)

    def reset(self):
        '''Reset values of attributes in order to perform multiple exec.'''
        self._tagged = False
        self.target = self._target_backup
        self.status = NO_STATUS
        self.algo_reversed = False

    def search(self, name, reverse=False):
        '''
        Search an entity through the overall graph. This recursive algorithm
        stops as soon as the node searched is reached.
        '''
        target = None
        deps = self.parents
        if reverse:
            deps = self.children
        if name in deps:
            return deps[name].target
        else:    
            for dep in deps.values():
                target = dep.target.search(name, reverse)
                if target:
                    return target
        return target

    def search_leafs(self, leafs=set(), reverse=False):
        '''
        Search entities which are leafs. Be a leaf means that the current
        entity has no parents/children (dependending on the reverse flag).
        This algorithm go through the overall graph.
        '''
        if self.children:
            deps = self.parents
            if self._algo_reversed:
                deps = self.children
            for dep in deps.values():
                dep.target.search_leafs(leafs, reverse)
        else:
            leafs.add(self)
        return leafs
        
    def add_dep(self, target, sgth=REQUIRE, parent=True):
        '''
        Add a dependency in both direction. This method allow the user to
        specify the dependency type. It is also possible to specify that
        the target is the parent or the child of the current entity.
        '''
        assert target, "target must not be None"
        if sgth in (CHECK, REQUIRE, REQUIRE_WEAK):
            if parent:
                if target.name in self.parents:
                    raise DependencyAlreadyReferenced()
                else:
                    # This dependency is considered as a parent
                    self.parents[target.name] = Dependency(target, sgth, False)
                    target.children[self.name] = Dependency(self, sgth, False)
            else:
                if target.name in self.children:
                    raise DependencyAlreadyReferenced()
                else:
                    # This dependency is considered as a child
                    self.children[target.name] = Dependency(target, sgth, False)
                    target.parents[self.name] = Dependency(self, sgth, False)
        else:
            raise IllegalDependencyTypeError()
            
    def remove_dep(self, dep_name, parent=True):
        '''
        Remove a dependency on both side, in the current object and in the
        target object concerned by the dependency.
        '''
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
        '''
        Determine whether the current object has a child dependency called
        dep_name.
        '''
        return dep_name in self.children
        
    def has_parent_dep(self, dep_name):
        '''
        Determine whether the current object has a parent dependency called
        dep_name
        '''
        return dep_name in self.parents
        
    def clear_deps(self):
        '''Clear parent/child dependencies.'''
        self.parents.clear()
        self.children.clear()
        
    def is_ready(self):
        '''
        Determine if the current services has to wait before to
        start due to unterminated dependencies.
        '''
        deps = self.parents
        if self._algo_reversed:
            deps = self.children
            
        for dep in deps.values():
            if dep.target.status in (NO_STATUS, WAITING_STATUS):
                return False
        return True

        
    def search_deps(self, symbols=None):
        '''
        Look for parent/child dependencies matching to the symbols. The
        search direction depends on the direction specified for the entiy.
        '''
        matching = []
        deps = self.parents
        if self._algo_reversed:
            deps = self.children  
        for dep_name in deps:
            if symbols and deps[dep_name].target.status in symbols:
                matching.append(deps[dep_name])
            elif not symbols:
                matching.append(deps[dep_name])
        return matching
    
    def eval_deps_status(self):
        '''
        Evaluate the result of the dependencies in order to check to establish
        a status.
        '''
        deps = self.parents
        if self._algo_reversed:
            deps = self.children

        temp_dep_status = DONE
        for dep in deps.values():
            if dep.target.status in (TOO_MANY_ERRORS, TIMED_OUT, ERROR):
                if dep.is_strong():
                    return ERROR
                elif temp_dep_status is not NO_STATUS:
                    temp_dep_status = DONE_WITH_WARNINGS
            elif dep.target.status is WAITING_STATUS:
                return WAITING_STATUS
            elif dep.target.status is DONE_WITH_WARNINGS and \
                temp_dep_status is not NO_STATUS:
                temp_dep_status = DONE_WITH_WARNINGS
            elif dep.target.status is NO_STATUS:
                temp_dep_status = NO_STATUS
        return temp_dep_status

    def set_algo_reversed(self, flag):
        '''Assign the right values for the property algo_reversed'''
        self._algo_reversed = flag

    algo_reversed = property(fset=set_algo_reversed)

    def get_target(self):
        '''Getter for the property target'''
        return self._target

    def set_target(self, nodeset):
        '''Setter for the property target'''
        self._target = NodeSet(nodeset)

    target = property(fget=get_target, fset=set_target)
    
