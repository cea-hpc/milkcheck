#
# Copyright CEA (2011-2012)
#
# This file is part of MilkCheck project.
#
# This software is governed by the CeCILL license under French law and
# abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# "http://www.cecill.info".
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and,  more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.

"""
This module contains the BaseEntity class definition
"""

# Classes
import re
import logging
from subprocess import Popen, PIPE
from ClusterShell.NodeSet import NodeSet

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
TIMEOUT = 'TIMEOUT'

# Error limit is overrun for the task performed by the entity 
ERROR = 'ERROR'

# Specify that the entity has an error
DEP_ERROR = 'DEP_ERROR'

# Specify that the entities is locked. An entity which is clocked
# cannot be processed by the engine.
LOCKED = 'LOCKED'

# Actions for this entity are not done and are skipped
SKIPPED = 'SKIPPED'

# Action is missing for this service and it was ignored
MISSING = 'MISSING'

DEP_ORDER = {
     DEP_ERROR      : 10,
     WAITING_STATUS : 9,
     NO_STATUS      : 8,
     WARNING        : 7,
     DONE           : 6,
     SKIPPED        : 5,
     MISSING        : 4,
     LOCKED         : 3
}

# Strength of a dependency
CHECK = "CHECK"
REQUIRE = "REQUIRE"
REQUIRE_WEAK = "REQUIRE_WEAK"


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

class VariableAlreadyExistError(MilkCheckEngineError):
    '''
    Exception raised as soon as you try to add a variable
    which is already defined for this entity.
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

class Dependency(object):
    '''
    This class define the structure of a dependency. A dependency can
    point both on parent and children. It models an edge between the
    two objects whithout considering their types.
    '''

    def __init__(self, target, dtype=REQUIRE, intr=False):

        # Object pointed by the dependency
        assert target, "Dependency target shall not be None"
        self.target = target

        # Define the type of the dependency
        assert dtype in (CHECK, REQUIRE, REQUIRE_WEAK), \
            "Invalid dependency identifier"
        self.dep_type = dtype

        # Allow us to consider the dependency as an internal
        # environment (e.g ServiceGroup)
        self._internal = intr

    def is_weak(self):
        '''Return True if the dependency is weak.'''
        return (self.dep_type == REQUIRE_WEAK)

    def is_strong(self):
        '''Return True if the dependency is strong'''
        return self.dep_type in (REQUIRE, CHECK)

    def is_check(self):
        '''Return True if the dependency is check'''
        return (self.dep_type == CHECK)

    def is_internal(self):
        '''Return the value of the internal attribute'''
        return self._internal

    def status(self):
        """Give entity status from a dependency point of view."""
        if self.target.status in (ERROR, TIMEOUT, DEP_ERROR):
            if self.is_strong():
                return DEP_ERROR
            else:
                return DONE
        else:
            return self.target.status

    def graph(self, source):
        """ Return DOT dependencies output for the given source"""
        tgt = self.target
        src = source

        dep_str = '"%s" -> "%s"' % (src.graph_info()[0],
                                    tgt.graph_info()[0])
        ginfo_target = tgt.graph_info()[1]
        ginfo_source = src.graph_info()[1]
        options = []
        if self.is_weak():
            options.append("style=dashed")
        if ginfo_source :
            options.append('ltail="%s"' % ginfo_source)
        if ginfo_target :
            options.append('lhead="%s"' % ginfo_target)
        if options:
            dep_str += " [%s]" % ",".join(options)

        dep_str += ";\n"

        return dep_str

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
        self.desc = None

        # Maximum window for parallelism. A None fanout means
        # that the task will be limited by the default value of
        # ClusterShell 64
        self.fanout = -1

        # Nodes on which the entity is launched
        self._target = None
        self.target = target
        self._target_backup = self.target

        # Special mode which change entity behaviour
        # 'delegate' means manage targets but run localy.
        self.mode = None

        # Maximum error authorized for the entity.
        self.errors = 0

        # Max time allowed to compute an entity, -1 means no timeout
        self.timeout = -1

        # Parent of the current object. Must be a subclass of BaseEntity
        self.parent = None

        # Parents dependencies (e.g A->B so B is the parent of A)
        self.parents = {}

        # Children dependencies (e.g A<-B) so A is a child of B)
        self.children = {}

        self.simulate = False

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
            raise VariableAlreadyExistError

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
            self.target.difference_update(nodeset)
        elif mode is 'INT' and self.target:
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
        for dpname in self.parents.keys():
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

    def deps(self):
        """
        Return parent dependency list.

        Return children deps as parent if algo is reversed.
        """
        if self._algo_reversed:
            return self.children
        else:
            return self.parents

    def is_ready(self):
        '''
        Determine if the current services has to wait before to
        start due to unterminated dependencies.
        '''
        for dep in self.deps().values():
            if dep.target.status in (NO_STATUS, WAITING_STATUS):
                return False
        return True 

    def search_deps(self, symbols=None):
        '''
        Look for parent/child dependencies matching to the symbols. The
        search direction depends on the direction specified for the entiy.
        '''
        # No selection criteria, return everything
        if not symbols:
            return self.deps().values()

        # Else, only keep matching deps
        else:
            dep_list = self.deps().values()
            return [dep for dep in dep_list if dep.target.status in symbols]

    def graph_info(self):
        """ Return a tuple to manage dependencies output """
        return (self.fullname(), None)

    def graph(self, excluded=None):
        """ Generate a graph of dependencies"""
        grph = ""
        # If the entity has a no dependency we just return the entity fullname
        if not self.deps().values():
            grph += '"%s";\n' % self.fullname()
        else:
            for dep in self.deps().values():
                if not dep.target.excluded(excluded):
                    if not dep.target.simulate:
                        grph += dep.graph(self)
                    else:
                        grph += '"%s";\n' % self.fullname()
        return grph

    def excluded(self, excluded=None):
        """Is the entity ecluded recusively"""
        if not excluded:
            return False
        if not self.deps().values():
            return self.fullname() in excluded

        # FIXME: Better loop detection
        if self.search(self.name):
            return True

        for dep in self.deps().values():
            if dep.target.excluded(excluded):
                return True

        return self.fullname() in excluded

    def eval_deps_status(self):
        '''
        Evaluate the result of the dependencies in order to check to establish
        a status.
        '''
        if len(self.deps()):
            order = lambda dep: DEP_ORDER[dep.status()]
            sorted_deps = sorted(self.deps().values(), key=order)
            return sorted_deps[-1].status()
        else:
            return MISSING

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

    def _substitute(self, template):
        """Substitute %xxx patterns from the provided template."""
        delimiter = '%'
        pattern = r"""
          %(delim)s(?:
            (?P<escaped>%(delim)s) | # Escape sequence of two delimiters
            (?P<named>%(id)s)      | # delimiter and a Python identifier
            {(?P<braced>%(id)s)}   | # delimiter and a braced identifier
            \((?P<parenth>.+)\)    | # delimiter and parenthesis
            (?P<invalid>)            # Other ill-formed delimiter exprs
          )""" % {
                'delim' : delimiter,
                'id' : r'[_a-z][_a-z0-9]*',
            }
        pattern = re.compile(pattern, re.IGNORECASE | re.VERBOSE)

        # Command substitution
        def _cmd_repl(raw):
            '''Replace a command execution pattern by its result.'''
            logger = logging.getLogger('milkcheck')
            cmd = Popen(raw, stdout=PIPE, stderr=PIPE, shell=True)
            stdout = cmd.communicate()[0]
            logger.debug("External command exited with %d: '%s'" %
                         (cmd.returncode, stdout))
            if cmd.returncode >= 126:
                raise InvalidVariableError(raw)
            return stdout.rstrip('\n')

        def _invalid(mobj, template):
            '''Helper to raise a detail error message'''
            i = mobj.start('invalid')
            lines = template[:i].splitlines(True)
            if not lines:
                colno = 1
                lineno = 1
            else:
                colno = i - len(''.join(lines[:-1]))
                lineno = len(lines)
            raise ValueError('Invalid placeholder in string: line %d, col %d' %
                             (lineno, colno))

        def _convert(mobj):
            """Helper function for .sub()"""
            # Check the mobjst commobjn path first.
            named = mobj.group('named') or mobj.group('braced')
            if named is not None:
                val = str(self._lookup_variable(named))
                return self._resolve(val)
            if mobj.group('escaped') is not None:
                return delimiter
            if mobj.group('parenth') is not None:
                val = self._resolve(mobj.group('parenth'))
                return _cmd_repl(val)
            if mobj.group('invalid') is not None:
                _invalid(mobj, template)
            raise ValueError('Unrecognized named group in pattern', pattern)
        return pattern.sub(_convert, template)

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
        if len(str(value)) == 0 or \
          not re.search('[\$%]\(.+\)|%\w+', str(value)):
            return value

        # Replace all %xxx patterns
        value = self._substitute(str(value))

        #
        # XXX: COMPAT CODE
        # Command substitution for oldstyle command repl: $(...)
        # This needs to be keep just the time required for people to migrate
        # from the old-style escaping.
        #
        def repl(pattern):
            '''Replace a command execution pattern by its result.'''
            cmd = Popen(pattern.group(1), stdout=PIPE, stderr=PIPE, shell=True)
            stdout = cmd.communicate()[0]
            logger.debug("External command exited with %d: '%s'" %
                         (cmd.returncode, stdout))
            if cmd.returncode >= 126:
                raise InvalidVariableError(pattern.group(1))
            return self._resolve(stdout.rstrip('\n'))
        value = re.sub('\$\((.+?)\)', repl, str(value))

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

        # Beware to check the default value of all of theses properties.
        # Some of theses have a two possible 'false' value (None or '').
        # * The init value should always be None
        # * '' is set by the user
        if self.fanout <= -1 and entity.fanout:
            self.fanout = entity.fanout
        self.errors = self.errors or entity.errors
        if self.timeout is not None and self.timeout <= -1 and \
            entity.timeout >= 0:
            self.timeout = entity.timeout
        if self.target is None:
            self.target = entity.target
        self.mode = self.mode or entity.mode
        if self.desc is None:
            self.desc = entity.desc

    def fromdict(self, entdict):
        """Populate entity attributes from dict."""

        for item, prop in entdict.items():
            if item == 'target':
                self.target = prop
                self._target_backup = prop
            elif item == 'mode':
                self.mode = prop
            elif item == 'fanout':
                self.fanout = prop
            elif item == 'timeout':
                self.timeout = prop
            elif item == 'errors':
                self.errors = prop
            elif item == 'desc':
                self.desc = prop
            elif item == 'variables':
                for varname, value in prop.items():
                    self.add_var(varname, value)

    def skipped(self):
        """Return if the Entity is SKIPPED"""
        return (self.target != None and len(self.target) == 0)

