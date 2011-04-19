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
from MilkCheck.Engine.BaseService import IN_PROGRESS, ERROR, TIMED_OUT
from MilkCheck.Engine.BaseService import TOO_MANY_ERRORS, SUCCESS_WITH_WARNINGS
from MilkCheck.Engine.Dependency import CHECK, REQUIRE, REQUIRE_WEAK

class ActionNotFoundError(MilkCheckEngineError):
    """
    Error raised as soon as the current service has not the action
    requested by the service.
    """
    
    def __init__(self, sname, aname):
        msg = "%s not referenced in %s" % (aname, sname) 
        MilkCheckEngineError.__init__(self, msg) 
        
class ActionAlreadyReferencedError(MilkCheckEngineError):
    """
    Error raised whether the current service already has an action
    with the same name.
    """
    def __init__(self, sname, aname):
        msg = "%s already referenced in %s" % (aname, sname) 
        MilkCheckEngineError.__init__(self, msg)

class Service(BaseService):
    """This class models a service ."""
    def __init__(self, name):
        BaseService.__init__(self, name)
        
        # Actions of the service
        self._actions = {}
        self._last_action = None
     
    def add_action(self, action):
        """Add a new action for the current service"""
        if action.name in self._actions:
            raise ActionAlreadyReferencedError(self.name, action.name)
        else:
            self._actions[action.name] = action
            
    def remove_action(self, action_name):
        """Remove the specified action from those available in the service."""
        if action_name in self._actions:
            del self._actions[action_name]
        else:
            raise ActionNotFoundError(self.name, action_name)
    
    def has_action(self, action_name):
        """Figure out whether the service has the specified action."""
        return action_name in self._actions
    
    def last_action(self):
        """
        Return the last action hooked/applied to the service. This action
        contain the worker of the last task performed.
        """
        if self._last_action and self.has_action(self._last_action):
            return self._actions[self._last_action]
        else:
            raise ActionNotFoundError(self.name, self._last_action)
    
    def add_dependency(self, service, dep_type=REQUIRE, internal=False):
        """Overrides the original behaviour of BaseService.add_dependency()"""
        assert not internal, "Cannot add an internal dependency to a Service"
        BaseService.add_dependency(self,service, dep_type)
           
    def _schedule_task(self, action_name):
        """
        Assign the content of the action to ClusterShell in using
        ClusterShell Task.
        """
        action = self._actions[action_name]
        action.worker = self._task.shell(action.command,
        nodes=action.target, handler=self, timeout=action.timeout)
        print "[%s] added to the master task" % self.name
       
    def prepare(self, action_name=None):
        """
        Prepare the the current service to be launched as soon
        as his dependencies are solved. 
        """
        if not action_name and self.has_action(self._last_action):
            action_name = self._last_action
        else:
            if self.has_action(action_name):
                self._last_action = action_name
            else:
                raise ActionNotFoundError(self.name, action_name)
        
        deps_status= self.eval_deps_status()
        
        # NO_STATUS and not any dep in progress for the current service
        if self.status == NO_STATUS and not deps_status == IN_PROGRESS:
            print "[%s] is preparing" % self.name
            
            # If dependencies failed the current service will fail
            if deps_status == ERROR:
                self.update_status(ERROR)
            else:
                # Just flag if dependencies encounter problem
                if deps_status == SUCCESS_WITH_WARNINGS:
                    self.warnings = True
                
                # Look for uncompleted dependencies 
                deps = self.search_deps([NO_STATUS])
                
                # For each existing deps just prepare it
                if deps:
                    for dep in deps:
                        if dep.is_check():
                            dep.target.prepare("status")
                        else:
                            dep.target.prepare(action_name)
                else:
                    # It's time to be processed
                    self.update_status(IN_PROGRESS)
                    self._schedule_task(action_name)
                
    def ev_hup(self, worker):
        """Called to indicate that a worker's connection has been closed."""
        pass
    
    def ev_close(self, worker):
        """
        Called to indicate that a worker has just finished (it may already
        have failed on timeout).
        """
        print "[%s] ev_close" % self.name
       
        cur_action = self.last_action()
        
        if cur_action.has_too_many_errors():
            self.update_status(TOO_MANY_ERRORS)
        else:
            if cur_action.has_timed_out():
                self.update_status(TIMED_OUT)
            else:
                if self.warnings:
                    self.update_status(SUCCESS_WITH_WARNINGS)
                else:
                    self.update_status(SUCCESS)
