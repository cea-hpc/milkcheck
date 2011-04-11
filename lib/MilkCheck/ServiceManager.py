# Copyright CEA (2011)  
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This module contains the ServiceManager class definition
"""

# Classes
from MilkCheck.Engine.Service import Service
from MilkCheck.Engine.Action import Action

# Exceptions
from MilkCheck.Engine.BaseEntity import MilkCheckEngineError

class ServiceNotFoundError(MilkCheckEngineError):
    """
    Define an exception raised when you are looking for a service
    that does not exist
    """
    
    def __init__(self, message="Service is not referenced by the manager"):
        """Constructor"""
        MilkCheckEngineError.__init__(self, message)

class ServiceManager(object):
    """
    The service manager has to handle call to services. It implements
    features allowing us to get dependencies of service and so son
    """
    def __init__(self):
        # Services handled by the manager
        self._services = {}
        
        # Variables declared in the global scope
        self._variables = {}
        
    def call_services(self, services_names, action_name, params=None):
        """
        Allow the user to call one or multiple services
        """
        for name in services_names:
            service = None
            normalized_name = name.lower()
            if self._services.has_key(normalized_name) is True:
                service = self._services[normalized_name]
                service.run(action_name)
            else:
                raise ServiceNotFoundError