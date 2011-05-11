# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This module contains the Service class definition
"""

# Classes
from MilkCheck.Engine.BaseService import BaseService
from MilkCheck.Engine.Action import Action

# Exceptions
from MilkCheck.Engine.BaseEntity import MilkCheckEngineError

# Symbols
from MilkCheck.Engine.BaseEntity import NO_STATUS, TOO_MANY_ERRORS
from MilkCheck.Engine.BaseEntity import WAITING_STATUS, ERROR, DONE
from MilkCheck.Engine.BaseEntity import DONE_WITH_WARNINGS, TIMED_OUT
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

    def reset(self):
        '''Reset values of attributes in order to perform multiple exec'''
        BaseService.reset(self)
        self._last_action = None
        for action in self._actions.values():
            action.reset()
    
    def add_action(self, action):
        """Add a new action for the current service"""
        if isinstance(action, Action):
            if action.name in self._actions:
                raise ActionAlreadyReferencedError(self.name, action.name)
            else:
                action.service = self
                self._actions[action.name] = action
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
    
    def schedule(self, action_name):
        """Schedule all required actions to perform the action"""
        # Retrieve targeted action
        self._actions[action_name].prepare()

    def update_status(self, status):
        """
        Update the current service's status and can trigger his dependencies.
        """
        assert status in (TIMED_OUT, TOO_MANY_ERRORS, DONE, \
                            DONE_WITH_WARNINGS, NO_STATUS, WAITING_STATUS, \
                                ERROR)

        if self.warnings and self.last_action().status is DONE:
            self.status = DONE_WITH_WARNINGS
        else:
            self.status = status

        print "[%s] is [%s]" % (self.name, self.status)

        # I got a status so I'm DONE or ERROR and I'm not the calling point
        if self.status not in (NO_STATUS, WAITING_STATUS) and not self.origin:

            # Trigger each service which depend on me as soon as it does not
            # have WAITING_STATUS parents
            deps = self.children
            if self._algo_reversed:
                deps = self.parents
                
            for dep in deps.values():
                if dep.target.status is NO_STATUS and \
                    dep.target.is_ready():
                    print  "(***) [%s] triggers [%s]" % (self.name, \
                        dep.target.name)
                    dep.target.prepare()

    def _process_dependencies(self, deps):
        '''perform a prepare on each dependencies in deps'''
        if deps:
            for dep in deps:
                if dep.is_check():
                    dep.target.prepare('status')
                else:
                    dep.target.prepare(self._last_action)
        else:
            # It's time to be processed
            self.update_status(WAITING_STATUS)
            self.schedule(self._last_action)

    def _action_checkpoint(self, action_name):
        '''
        Check that the service will get a call to an existing action.
        if you reference a none existing action ActionNotFoundError is raised.
        '''
        if not action_name and self.has_action(self._last_action):
            action_name = self._last_action
        elif action_name and self.has_action(action_name):
            self._last_action = action_name
        else:
            raise ActionNotFoundError(self.name, action_name)
    
    def prepare(self, action_name=None):
        """
        Prepare the the current service to be launched as soon
        as his dependencies are solved. 
        """
        #print "[%s] is working" % self.name
        self._action_checkpoint(action_name)
        deps_status = self.eval_deps_status()

        # NO_STATUS and not any dep in progress for the current service
        if self.status == NO_STATUS and not deps_status == WAITING_STATUS:
            #print "[%s] is working" % self.name
            
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
                self._process_dependencies(deps)
                
            #print "[%s] prepare end" % self.name
        #print "[%s] prepare end" % self.name