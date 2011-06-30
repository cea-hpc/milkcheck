# Copyright CEA (2011)
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This module contains the EntityManager class definition.
"""

class EntityManager(object):
    """
    This class defines the most basic type of manager. A manager
    allow us to handle whichever type of objects
    """
    _instance = None

    def __init__(self):
        # entity handle by the manager
        self.entities = {}

    def iter_entities(self):
        '''Return an iterator over the entitie'''
        return self.entities.itervalues()

    def _reverse_mod(self, flag):
        """
        Enable a flag on BaseEntity object which help us to define
        the algorithm direction
        """
        assert flag in (True, False), 'Invalid flag'
        for entity in self.entities.values():
            entity.algo_reversed = flag

def entity_manager_self():
    """Return a singleton instance of the entity manager"""
    if not EntityManager._instance:
        EntityManager._instance = EntityManager()
    return EntityManager._instance