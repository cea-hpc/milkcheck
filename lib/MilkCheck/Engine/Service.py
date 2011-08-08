# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This module contains the Service class definition
"""

# Classes
from MilkCheck.Engine.BaseService import BaseService
from MilkCheck.Engine.Action import Action
from MilkCheck.Engine.BaseEntity import BaseEntity
from MilkCheck.Callback import call_back_self

# Exceptions
from MilkCheck.Engine.BaseEntity import MilkCheckEngineError

# Symbols
from MilkCheck.Engine.BaseEntity import NO_STATUS, TOO_MANY_ERRORS
from MilkCheck.Engine.BaseEntity import WAITING_STATUS, ERROR, DONE
from MilkCheck.Engine.BaseEntity import WARNING, TIMED_OUT
from MilkCheck.Callback import EV_STATUS_CHANGED, EV_TRIGGER_DEP

class ActionNotFoundError(MilkCheckEngineError):
    '''
    Error raised as soon as the current service has not the action
    requested by the service.
    '''
    
    def __init__(self, sname, aname):
        msg = "Action [%s] not referenced for [%s]" % (aname, sname)
        MilkCheckEngineError.__init__(self, msg) 
        
class ActionAlreadyReferencedError(MilkCheckEngineError):
    '''
    Error raised whether the current service already has an action
    with the same name.
    '''
    def __init__(self, sname, aname):
        msg = "%s already referenced in %s" % (aname, sname) 
        MilkCheckEngineError.__init__(self, msg)

class Service(BaseService):
    '''
    This class is a concrete representation of the concept of Service
    introduced by BaseSevice. A Service contains actions, and those actions
    are called and executed on nodes.
    '''

    LOCAL_VARIABLES = BaseService.LOCAL_VARIABLES.copy()
    LOCAL_VARIABLES['SERVICE'] = 'name'

    def __init__(self, name, target=None):
        BaseService.__init__(self, name, target)

        # Actions of the service
        self._actions = {}
        self._last_action = None

    def update_target(self, nodeset, mode=None):
        '''Update the attribute target of a service'''
        assert nodeset, 'The nodeset cannot be None'
        if not mode:
            self.target = nodeset
        elif mode is 'DIF':
            self.target.difference_update(nodeset)
        elif mode is 'INT':
            self.target.intersection_update(nodeset)
        for action in self._actions.values():
            action.update_target(nodeset, mode)

    def reset(self):
        '''Reset values of attributes in order to perform multiple exec'''
        BaseService.reset(self)
        self._last_action = None
        for action in self._actions.values():
            action.reset()

    def add_action(self, action):
        '''Add a new action to the service'''
        if isinstance(action, Action):
            if action.name in self._actions:
                raise ActionAlreadyReferencedError(self.name, action.name)
            else:
                action.parent = self
                self._actions[action.name] = action
        else:
            raise TypeError()

    def add_actions(self, *args):
        '''Add multiple actions to the service'''
        for action in args:
            self.add_action(action)

    def iter_actions(self):
        '''Return an iterator over actions'''
        return self._actions.itervalues()

    def remove_action(self, action_name):
        '''Remove the specified action from those available in the service.'''
        if action_name in self._actions:
            del self._actions[action_name]
        else:
            raise ActionNotFoundError(self.name, action_name)

    def has_action(self, action_name):
        '''Figure out whether the service has the specified action.'''
        return action_name in self._actions

    def last_action(self):
        '''
        Return the last action hooked/applied to the service. This action
        contain the worker of the last task performed.
        '''
        if self._last_action and self.has_action(self._last_action):
            return self._actions[self._last_action]
        else:
            raise ActionNotFoundError(self.name, self._last_action)

    def schedule(self, action_name):
        '''Schedule an action available for this service'''
        # Retrieve targeted action
        self._actions[action_name].prepare()

    def update_status(self, status):
        '''
        Update the current service's status and whether all of his parents
        dependencies are solved start children dependencies.
        '''
        assert status in (TIMED_OUT, TOO_MANY_ERRORS, DONE, \
                            WARNING, NO_STATUS, WAITING_STATUS, \
                                ERROR)

        if self.warnings and self.last_action().status is DONE:
            self.status = WARNING
        else:
            self.status = status

        if not self.simulate:
            call_back_self().notify(self, EV_STATUS_CHANGED)

        # I got a status so I'm DONE or ERROR and I'm not the calling point
        if self.status not in (NO_STATUS, WAITING_STATUS) and \
            not self.origin:

            # Trigger each service which depend on me as soon as it does not
            # have WAITING_STATUS parents
            deps = self.children
            if self._algo_reversed:
                deps = self.parents

            for dep in deps.values():
                if dep.target.status is NO_STATUS and \
                    dep.target.is_ready() and \
                        dep.target._tagged:
                    if not self.simulate:
                        call_back_self().notify((self, dep.target),
                        EV_TRIGGER_DEP)
                    dep.target.prepare()

    def _process_dependencies(self, deps):
        '''Perform a prepare on each dependency in deps'''
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
        '''
        Prepare the the current service to be launched as soon
        as his dependencies are solved. 
        '''
        self._action_checkpoint(action_name)
        deps_status = self.eval_deps_status()
        # Tag the service
        self._tagged = True

        # NO_STATUS and not any dep in progress for the current service
        if self.status is NO_STATUS and deps_status is not WAITING_STATUS:

            # If dependencies failed the current service will fail
            if deps_status == ERROR:
                self.update_status(ERROR)
            else:
                # Just flag if dependencies encountered problem
                if deps_status == WARNING:
                    self.warnings = True

                # Look for uncompleted dependencies 
                deps = self.search_deps([NO_STATUS])

                # For each existing deps just prepare it
                self._process_dependencies(deps)

    def inherits_from(self, entity):
        '''Inherit properties from entity'''
        BaseEntity.inherits_from(self, entity)
        for action in self.iter_actions():
            action.inherits_from(self)
