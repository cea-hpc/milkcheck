# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This module contains the Service class definition
"""

# Classes
from copy import copy
from MilkCheck.Engine.BaseService import BaseService
from MilkCheck.Engine.Action import Action

# Exceptions
from MilkCheck.Engine.BaseEntity import MilkCheckEngineError

# Symbols
from MilkCheck.Engine.BaseEntity import NO_STATUS
from MilkCheck.Engine.BaseEntity import WAITING_STATUS, ERROR
from MilkCheck.Engine.BaseEntity import DONE_WITH_WARNINGS
from MilkCheck.Engine.Dependency import REQUIRE

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
        if isinstance(action, Action):
            if action.name in self._actions:
                raise ActionAlreadyReferencedError(self.name, action.name)
            else:
                action.parent = self
                self._actions[action.name] = copy(action)
        else:
            raise TypeError()
     
    def add_actions(self, *args):
        """Add multiple actions at the same type"""
        for action in args:
            self.add_action(action)
            
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
    
    def add_dep(self, target, sgth=REQUIRE, parent=True, inter=False):
        """Overrides the original behaviour of BaseService.add_dependency()"""
        assert not inter, "Cannot add an internal dependency to a Service"
        BaseService.add_dep(self, target, sgth, parent)
    
    def _schedule_task(self, action_name):
        """
        Schedule all required actions to perform the action
        """
        # Retrieve targeted action
        action = self._actions[action_name]
        
        # Fire all actions depending in action
        if action.parents:
            for child in action.parents.values():
                child.target.schedule(paction=action)
        else:
            # Fire the main action
            action.schedule()
       
    def prepare(self, action_name=None, reverse=False):
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
        
        deps_status = self.eval_deps_status()
        
        # NO_STATUS and not any dep in progress for the current service
        if self.status == NO_STATUS and not deps_status == WAITING_STATUS:
            print "[%s] is preparing" % self.name
            
            # If dependencies failed the current service will fail
            if deps_status == ERROR:
                self.update_status(ERROR)
            else:
                # Just flag if dependencies encountered problem
                if deps_status == DONE_WITH_WARNINGS:
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
                    self.update_status(WAITING_STATUS)
                    self._schedule_task(action_name)