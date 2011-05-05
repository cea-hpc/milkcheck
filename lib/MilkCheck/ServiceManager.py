# Copyright CEA (2011)  
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This module contains the ServiceManager class definition.
"""

# Classes
from ClusterShell.Task import task_self
from MilkCheck.EntityManager import EntityManager

# Exceptions
from MilkCheck.Engine.BaseEntity import MilkCheckEngineError

class ServiceNotFoundError(MilkCheckEngineError):
    """
    Define an exception raised when you are looking for a service
    that does not exist.
    """
    def __init__(self, message="Service is not referenced by the manager"):
        """Constructor"""
        MilkCheckEngineError.__init__(self, message)

class ServiceManager(EntityManager):
    """
    The service manager has to handle call to services. It implements
    features allowing us to get dependencies of service and so on.
    """
    
    def __init__(self):
        
        # Variables declared in the global scope
        self._variables = {}
        
    def call_services(self, services_names, action_name, params=None):
        """Allow the user to call one or multiple services."""
        for name in services_names:
            service = None
            normalized_name = name.lower()
            if self._entities.has_key(normalized_name):
                self._services[normalized_name].run(action_name)
            else:
                raise ServiceNotFoundError()
    
    def dependencies(self, service_name):
        pass

def service_manager_self():
    """Return a singleton instance of a service manager"""
    if not ServiceManager._instance:
        ServiceManager._instance = ServiceManager()
    return ServiceManager._instance