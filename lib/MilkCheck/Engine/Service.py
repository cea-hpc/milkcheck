# coding=utf-8
# Copyright CEA (2011) 
# Contributor: TATIBOUET Jérémie <tatibouetj@ocre.cea.fr>

"""
This module contains the Service class definition
"""

# Classes
from MilkCheck.Engine.BaseService import BaseService

# Errors
from MilkCheck.Engine.Action import ActionAlreadyReferencedError
from MilkCheck.Engine.Action import ActionNotFoundError

# Symbols
from MilkCheck.Engine.BaseService import NO_STATUS, SUCCESS, IN_PROGRESS

class Service(BaseService):
    
    """
    This class models a service
    """
    
    def __init__(self, name):
        """
        Service constructor
        """
        BaseService.__init__(self, name)
        
        # Actions of the service
        self._actions = {}
     
    def add_action(self, action):
        """
        Add a new action for the current service
        """
        if action in self._actions:
            raise ActionAlreadyReferencedError(self.name, action)
        else:
            self._actions[action.name] = action
            
    def remove_action(self, action):
        """
        Remove the specified action from those available in the service
        """
        if action in self._actions:
            del self._actions[action]
        else:
            raise ActionNotFoundError()
    
    def has_action(self, action_name):
        """
        Figures out whether the service  has the specified action
        """
        return action_name in self._actions
    
    def _schedule_task(self, action_name):
        """
        Assigns the content of the action to ClusterShell in using
        ClusterShell Task
        """
        action = self._actions[action_name]
        self._task.shell(action.command, nodes=action.target,
            handler=self)

        
     #testing
    def prepare(self, action_name=None):
        """
        Checks that the service has the required action
        """
        if self.has_action(action_name):
            """
            Looks for the depencies which are not solved and 
            adds the service to the queue of tasks
            """
            print "%s is preparing" % self.name
           
            if self.status == NO_STATUS:
                
                
                """
                If some of my dependencies have no status
                so I have to ask them to be prepared
                """
                deps = self._remaining_dependencies()
                
                if deps:
                    
                    print "%s has parents without status" % self.name
                    
                    for (service, dtype, obl) in deps:
                        if dtype == "check":
                            service.prepare("status")
                        else:
                            service.prepare(action_name)
                else:
                    """
                    All of my dependencies ar solved so I can be
                    processed by the task
                    """
                    self.update_status(IN_PROGRESS)
                    self._schedule_task(action_name)
        else:
            raise ActionNotFoundError(self.name, action_name)
