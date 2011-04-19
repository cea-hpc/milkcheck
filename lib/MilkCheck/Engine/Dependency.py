# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This module contains the definition of the Dependency object and the
symbols linked.
"""

# Exceptions
from MilkCheck.Engine.BaseEntity import MilkCheckEngineError

# Symbols
CHECK = "CHECK"
REQUIRE = "REQUIRE"
REQUIRE_WEAK = "REQUIRE_WEAK"

class IllegalDependencyTypeError(MilkCheckEngineError):
    """
    Exception raised when you try to assign another identifier than
    CHECK, REQUIRE OR REQUIRE_WEAK to dep_type
    """

class Dependency(object):
    """This class define the structure of a dependency."""
    
    def __init__(self, target, dep_type=REQUIRE, internal=False):
        
        
        # Object of caracterised by the dependency
        assert target, "should not be be None"
        self.target = target
        
        # The type of the dependency can be
        # - CHECK (always strong)
        # - REQUIRE (either strong or weak)
        assert dep_type in (CHECK, REQUIRE, REQUIRE_WEAK), \
            "Invalid dependency identifier"
        self._dep_type = dep_type
        
        # An dependency can be internal (ServiceGroup)
        self._internal = internal
        
    def is_weak(self):
        """ Return True if the dependency is weak."""
        return (self._dep_type == REQUIRE_WEAK)
    
    def is_strong(self):
        """Return True if the dependency is strong"""
        return self._dep_type in (REQUIRE, CHECK)
    
    def is_check(self):
        """Return True if the dependency is check"""
        return (self._dep_type == CHECK)
    
    def is_internal(self):
        """Return the value of the internal attribute"""
        return self._internal

    def  set_dep_type(self, d_type):
        """Change the type of the dependency"""
        if d_type in (CHECK, REQUIRE, REQUIRE_WEAK):
            self._dep_type = d_type
        else:
            raise IllegalDependencyTypeError()
       
    dep_type = property(fset=set_dep_type)