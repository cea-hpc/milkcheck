#coding=utf-8
#copyright CEA (2011) 
#contributor: TATIBOUET Jérémie <tatibouetj@ocre.cea.fr>

"""
This module contains the Action class definition
"""

from MilkCheck.Engine.BaseEntity import BaseEntity
from MilkCheck.Engine.BaseService import MilkCheckEngineException
from ClusterShell.Worker.Worker import Worker

class Action(BaseEntity):
    """
    This class models an action. An action can be applied to a service
    and contain the code that we need to execute on nodes specified in the
    action or service
    """
    
    def __init__(self, name):
        """
        Constructor of an Action
        """
        BaseEntity.__init__(self, name)
        
        #action's timeout in seconds
        self.timeout = 0
        
        #action's delay in seconds
        self.delay = 0
        
        #number of action's retry
        self.retry = 0
        
        # Command lines that we would like to run 
        self.command = ""
        
        #results and retcodes
        self.worker = None
        
class ActionNotFoundError(MilkCheckEngineException):
    """
    Action raised as soon as the current service has not the action
    requested by the service
    """
    
    def __init__(self, sname, aname):
        """Constructor"""
        msg = str(aname)+" not referenced in "+str(sname) 
        MilkCheckEngineException.__init__(self, msg) 
        
class ActionAlreadyReferencedError(MilkCheckEngineException):
    """
    Action raised as soon as the current service has not the action
    requested by the service
    """
    
    def __init__(self, sname, aname):
        """Constructor"""
        msg = str(aname)+" already referenced in "+str(sname) 
        MilkCheckEngineException.__init__(self, msg) 