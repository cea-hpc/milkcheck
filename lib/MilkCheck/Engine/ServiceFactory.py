# coding=utf-8
# Copyright CEA (2011) 
# Contributor: TATIBOUET Jérémie <tatibouetj@ocre.cea.fr>

"""
This module contains the ServiceFactory class definition
"""

class ServiceFactory(object):

    """
    This class allow us to build a Service or ServiceGroup thanks
    to a dictionnary.
    """

    # Unik instance
    _instance = None
   
    def __new__(self, *args, **kwargs):
        """control of singleton pattern"""
        if self._instance is None:
            self._instance = super(ServiceFactory, self).__new__(
                                self, *args, **kwargs)
        return self._instance 
   
    def __init__(self):
        """constructor of the service Factory"""
        pass
    
    def create_service(serialized_service):
        """Return the created service based on the provided dictionnary."""
        
        
    def create_service_group(service):
        """returns the created service group"""