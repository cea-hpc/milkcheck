# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This module contains the Action class definition
"""

from MilkCheck.Engine.BaseEntity import BaseEntity
from ClusterShell.Worker.Worker import Worker

class Action(BaseEntity):
    """
    This class models an action. An action can be applied to a service
    and contain the code that we need to execute on nodes specified in the
    action or service
    """
    
    def __init__(self, name):
        BaseEntity.__init__(self, name)
        
        # Action's timeout in seconds
        self.timeout = 0
        
        # Action's delay in seconds
        self.delay = 0
        
        # Number of action's retry
        self.retry = 0
        
        # Command lines that we would like to run 
        self.command = ""
        
        # Results and retcodes
        self.worker = None