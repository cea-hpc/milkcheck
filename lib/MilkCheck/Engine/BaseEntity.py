# Copyright CEA (2011)  
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This module contains the BaseEntity class definition
"""

# Classes
import logging
import string
from subprocess import Popen, PIPE
from re import sub, search
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
WARNING = 'WARNING'

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

# Actions for this entity are not done and are skipped
SKIPPED = 'SKIPPED'

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

class VariableAlreadyReferencedError(MilkCheckEngineError):
    '''
    Exception raised as soon as you try to add a variable
    which is already referenced for this entity.
    '''

class UndefinedVariableError(MilkCheckEngineError):
    '''
    This error is raised each time that you make reference to a None existing
    variable located in a command
    '''
    def __init__(self, varname):
        msg = "Variable %s undefined" % varname
        MilkCheckEngineError.__init__(self, msg)

class InvalidVariableError(MilkCheckEngineError):
    '''
    This error is raised when wer try to evaluate the value of a variables
    through the shell but the retcode is greater than one.
    '''
    def __init__(self, varname):
        msg = "Cannot evaluate expression '%s'" % varname
        MilkCheckEngineError.__init__(self, msg)

class BaseEntity(object):
    '''
    This class is abstract and shall not be instanciated.
    A BaseEntity object basically represents a node of graph with reference
    on parents and children.
    '''

    LOCAL_VARIABLES = {
        'NAME':    'name',
        'FANOUT':  'fanout',
        'TIMEOUT': 'timeout',
        'TARGET':  'target',
        'DESC':    'desc',
    }

    def __init__(self, name, target=None):
        # Entity name
        self.name = name

        # Each entity has a status which it state
        self.status = NO_STATUS

        # Description of an entity
        self.desc = ''

        # Maximum window for parallelism. A None fanout means
        # that the task will be limited by the default value of
        # ClusterShell 64
        self.fanout = -1

        # Nodes on which the entity is launched
        self.target = target
        self._target_backup = self.target

        # Special mode which change entity behaviour
        # 'delegate' means manage targets but run localy.
        self.mode = None

        # Maximum error authorized for the entity. -1 means that
        # we do not want any error
        self.errors = -1

        # Max time allowed to compute an entity, -1 means no timeout
        self.timeout = -1

        # Parent of the current object. Must be a subclass of BaseEntity
        self.parent = None

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

        # Variables
        self.variables = {}

    def add_var(self, varname, value):
        '''Add a new variable within the entity context'''
        if varname not in self.variables:
            self.variables[varname] = value
        else:
            raise VariableAlreadyReferencedError

    def remove_var(self, varname):
        '''Remove an existing var from the entity'''
        if varname in self.variables:
            del self.variables[varname]

    def update_target(self, nodeset, mode=None):
        '''Update the attribute target of an entity'''
        assert nodeset, 'The nodeset cannot be None'
        if not mode:
            self.target = NodeSet(nodeset)
        elif mode is 'DIF' and self.target:
            self.target = NodeSet(self.resolve_property('target'))
            self.target.difference_update(nodeset)
        elif mode is 'INT' and self.target:
            self.target = NodeSet(self.resolve_property('target'))
            self.target.intersection_update(nodeset)

    def get_target(self):
        '''Return self._target'''
        return self._target

    def set_target(self, value):
        '''Assign nodeset to _target'''
        self._target = None
        if value is not None:
            self._target = NodeSet(self._resolve(value))

    target = property(fset=set_target, fget=get_target)

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

    def clear_parent_deps(self):
        '''Remove all parent dependencies of an entity'''
        for dpname in self.children.keys():
            self.remove_dep(dpname)

    def clear_child_deps(self):
        '''Remove all child dependencies of an entity'''
        for dpname in self.children.keys():
            self.remove_dep(dep_name=dpname, parent=False)

    def has_child_dep(self, dep_name=None):
        '''
        Determine whether the current object has a child dependency called
        dep_name.
        '''
        return dep_name in self.children

    def has_parent_dep(self, dep_name=None):
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
                    temp_dep_status = WARNING
            elif dep.target.status is WAITING_STATUS:
                return WAITING_STATUS
            elif dep.target.status is WARNING and \
                temp_dep_status is not NO_STATUS:
                temp_dep_status = WARNING
            elif dep.target.status is NO_STATUS:
                temp_dep_status = NO_STATUS
        return temp_dep_status

    def set_algo_reversed(self, flag):
        '''Assign the right values for the property algo_reversed'''
        self._algo_reversed = flag

    algo_reversed = property(fset=set_algo_reversed)

    def longname(self):
        '''Return entity fullname and descrition if available '''
        label = self.fullname()
        if self.desc:
            label += " - %s" % self.desc
        return label

    def fullname(self):
        '''Return the fullname of the current entity'''
        names = []
        if self.parent:
            names.append(self.parent.fullname())
        names.append(self.name)
        return '.'.join(names)

    def _lookup_variable(self, varname):
        '''
        Return the value of the specified variable name.

        If is not found in current object, it searches recursively in the
        parent object.
        If it cannot solve the variable name, it raises UndefinedVariableError.
        '''
        from MilkCheck.ServiceManager import service_manager_self

        if varname in self.variables:
            return self.variables[varname]
        elif varname.upper() in self.LOCAL_VARIABLES:
            value = self.LOCAL_VARIABLES[varname.upper()]
            return self._resolve(getattr(self, value))
        elif self.parent:
            return self.parent._lookup_variable(varname)
        elif varname in service_manager_self().variables:
            return service_manager_self().variables[varname]
        else:
            raise UndefinedVariableError(varname)

    def _resolve(self, value):
        '''
        This method takes a string containing symbols. Those strings may
        look like to : 
            + $(nodeset -f epsilon[5-8] -x epsilon7)
            + %CMD echo $(nodeset -f epsilon[5-8])
            + ps -e | grep myprogram
        After computation this method return a string with all the symbols
        resolved.
        The '%' character could be inserted using '%%'.
        '''
        origvalue = value
        logger = logging.getLogger('milkcheck')

        # For compat: if provided value is not a str, we should not convert
        # it to a str if nothing matches.
        # XXX: Are we sure we want this behaviour?
        if len(str(value)) == 0 or not search('\$\(.+\)|%\w+', str(value)):
            return value

        # Perform variable replacement
        class _MyTemplate(string.Template):
            """Implement MilkCheck variable syntax templating."""
            delimiter = '%'
        class _VarSource(dict):
            """Simulate a dict which each item is a variable lookup."""
            def __init__(self, entity):
                dict.__init__(self)
                self._entity = entity
            def __getitem__(self, item):
                value = str(self._entity._lookup_variable(item))
                return self._entity._resolve(value)
        value = _MyTemplate(str(value)).substitute(_VarSource(self))

        # Command substitution
        def repl(pattern):
            '''Replace a command execution pattern by its result.'''
            cmd = Popen(pattern.group(1), stdout=PIPE, stderr=PIPE, shell=True)
            stdout = cmd.communicate()[0]
            logger.debug("External command exited with %d: '%s'" %
                         (cmd.returncode, stdout))
            if cmd.returncode >= 126:
                raise InvalidVariableError(pattern.group(1))
            return self._resolve(stdout.rstrip('\n'))
        value = sub('\$\((.+?)\)', repl, str(value))

        # Replace escape caracter '%'
        value = sub('%%', '%', str(value))

        # Debugging
        if origvalue != value:
            logger.info("Variable content '%s' replaced by '%s'",
                        origvalue, value)

        return value

    def resolve_property(self, prop):
        '''
        Resolve the variables contained within the property. It proceeds by
        looking for the values required to replace the symbols. This method
        returns None whether the property does not exist.
        '''
        pvalue = None
        if hasattr(self, prop):
            pvalue = self._resolve(getattr(self, prop))
        return pvalue

    def inherits_from(self, entity):
        '''Inheritance of properties between entities'''
        if self.fanout <= -1 and entity.fanout:
            self.fanout = entity.fanout
        if self.errors <= -1 and entity.errors >= 0:
            self.errors = entity.errors
        if self.timeout is not None and self.timeout <= -1 and \
            entity.timeout >= 0:
            self.timeout = entity.timeout
        if not self.target:
            self.target = entity.target
        self.mode = self.mode or entity.mode
