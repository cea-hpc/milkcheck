# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This module contains the Service class definition
"""

# Classes
from MilkCheck.Engine.BaseService import BaseService

# Exceptions
from MilkCheck.Engine.BaseEntity import MilkCheckEngineError

# Symbols
from MilkCheck.Engine.BaseService import NO_STATUS, SUCCESS
from MilkCheck.Engine.BaseService import IN_PROGRESS, ERROR

class ActionNotFoundError(MilkCheckEngineError):
    """
    Action raised as soon as the current service has not the action
    requested by the service
    """
    
    def __init__(self, sname, aname):
        """Constructor"""
        msg = str(aname)+" not referenced in "+str(sname) 
        MilkCheckEngineError.__init__(self, msg) 
        
class ActionAlreadyReferencedError(MilkCheckEngineError):
    """
    Action raised as soon as the current service has not the action
    requested by the service
    """
    def __init__(self, sname, aname):
        msg = str(aname)+" already referenced in "+str(sname) 
        MilkCheckEngineError.__init__(self, msg) 

class Service(BaseService):
    """
    This class models a service
    """
    def __init__(self, name):
        BaseService.__init__(self, name)
        
        # Actions of the service
        self._actions = {}
        self._last_action = None
     
    def add_action(self, action):
        """
        Add a new action for the current service
        """
        if action.name in self._actions:
            raise ActionAlreadyReferencedError(self.name, action)
        else:
            self._actions[action.name] = action
            
    def remove_action(self, action_name):
        """
        Remove the specified action from those available in the service
        """
        if action_name in self._actions:
            del self._actions[action_name]
        else:
            raise ActionNotFoundError(self.name, action_name)
    
    def has_action(self, action_name):
        """
        Figure out whether the service  has the specified action
        """
        return action_name in self._actions
    
    def last_action(self):
        """
        Return the last action hooked/applied to the service. This action
        contains the worker of the last task performed
        """
        if self._last_action and self.has_action(self._last_action):
            return self._actions[self._last_action]
        else:
            raise ActionNotFoundError(self.name, self._last_action)
        
    def _schedule_task(self, action_name):
        """
        Assign the content of the action to ClusterShell in using
        ClusterShell Task
        """
        action = self._actions[action_name]
        if action.timeout <= 0:
            action.worker = self._task.shell(action.command,
                nodes=action.target,handler=self)
        else:
             action.worker = self._task.shell(action.command,
                nodes=action.target, handler=self, timeout=action.timeout)
        print "["+self.name+"] added to the master task" 
    
     #testing
    def prepare(self, action_name=None):
        """
        Prepare the the current service to be launched as soon
        as his dependencies are solved 
        """
        if not action_name and self.has_action(self._last_action):
            action_name = self._last_action
        else:
            if self.has_action(action_name):
                self._last_action = action_name
            else:
                raise ActionNotFoundError(self.name,action_name)
            
        # Looks for the depencies which are not solved and 
        # adds the service to the queue of tasks
        print "[%s] is preparing" % self.name
    
        if self.status == NO_STATUS:
        
            # If some of my dependencies have no status
            # so I have to ask them to be prepared
            
            deps = self._remaining_dependencies()
            
            if deps:
                
                print "[%s] has uncomplete parents" % self.name
                
                for (serv, dtype, obl) in deps:
                    
                    # Prepare only those which have no state
                    if serv.status == NO_STATUS:
                        if dtype == "check":
                            serv.prepare("status")
                        else:
                            serv.prepare(action_name)
            else:
                
                # All of my dependencies are solved so I can be
                # processed by the task
                self.update_status(IN_PROGRESS)
                self._schedule_task(action_name)
                 
    def ev_hup(self, worker):
        """
        Called to indicate that a worker's connection has been closed.
        """
        print "[%s] connection closed" % self.name
    
    def ev_close(self, worker):
        """
        Called to indicate that a worker has just finished (it may already
        have failed on timeout).
        """
        
        print "[%s] ev_close" % self.name
       
        cur_action = self.last_action()
        
        if cur_action.has_too_many_errors():
            self.update_status(ERROR)
        else:
            if cur_action.has_timed_out():
                self.update_status(ERROR)
            else:
                self.update_status(SUCCESS)
