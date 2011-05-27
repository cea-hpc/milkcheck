# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This module contains the definition of the Dependency object and the
symbols linked.
"""

# Symbols - strength of a dependency
CHECK = "CHECK"
REQUIRE = "REQUIRE"
REQUIRE_WEAK = "REQUIRE_WEAK"

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
        self._dep_type = dtype
        
        # Allow us to consider the dependency as an internal
        # environment (e.g ServiceGroup)
        self._internal = intr
        
    def is_weak(self):
        '''Return True if the dependency is weak.'''
        return (self._dep_type == REQUIRE_WEAK)
    
    def is_strong(self):
        '''Return True if the dependency is strong'''
        return self._dep_type in (REQUIRE, CHECK)
    
    def is_check(self):
        '''Return True if the dependency is check'''
        return (self._dep_type == CHECK)
    
    def is_internal(self):
        '''Return the value of the internal attribute'''
        return self._internal

    def set_dep_type(self, dtype):
        """Change the type of the dependency"""
        assert dtype in (CHECK, REQUIRE, REQUIRE_WEAK), \
        "Invalid dependency type"
        self._dep_type = dtype
        
    dep_type = property(fset=set_dep_type) 