# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This module contains the definition of the Base class of a service and the
defnition of the different states that a service can go through
"""

# Classes
from MilkCheck.Engine.BaseEntity import BaseEntity
from ClusterShell.Task import task_self

class BaseService(BaseEntity):
    '''
    This abstract class defines the concept of service. A Service might be
    a node of graph because it inherit from the properties and methods of
    BaseEntity. BaseService basically defines the main methods that derived
    Services types have to implements.
    '''
    
    def __init__(self, name):
        BaseEntity.__init__(self, name)
        
        # Define whether the service has warnings
        self.warnings = False
        
        # Define a flag allowing us to specify that this service
        # is the original caller so we do not have to start his
        # children 
        self.origin = False

        # Used for ghost services or services that you do not want to execute
        self.simulate = False

    def reset(self):
        '''Reset values of attributes in order to perform multiple exec'''
        BaseEntity.reset(self)
        self.warnings = False
        self.origin = False

    def run(self, action_name):
        '''Run an action over a service'''
        
        # A service using run become the calling point
        self.origin = True
        
        # Prepare the service and start the master task
        self.prepare(action_name)
        task_self().resume()
        
    def prepare(self, action_name=None):
        '''
        Recursive method allowing to prepare a service before his execution.
        The preparation of a service consist in checking that all of the
        dependencies linked to this service were solved. As soon as possible
        action requested will be started.
        '''
        raise NotImplementedError

    def update_status(self, status):
        '''
        Update the current service's status and whether all of his parents
        dependencies are solved start children dependencies.
        '''
        raise NotImplementedError