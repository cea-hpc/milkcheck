# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This module contains the Service class definition
"""

# Classes
from ClusterShell.NodeSet import NodeSet
from MilkCheck.Engine.BaseService import BaseService
from MilkCheck.Engine.Action import Action
from MilkCheck.Engine.BaseEntity import BaseEntity
from MilkCheck.Callback import call_back_self

# Exceptions
from MilkCheck.Engine.BaseEntity import MilkCheckEngineError

# Symbols
from MilkCheck.Engine.BaseEntity import NO_STATUS, WARNING, MISSING, SKIPPED
from MilkCheck.Engine.BaseEntity import WAITING_STATUS, DEP_ERROR, DONE
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
        elif mode is 'DIF' and self.target:
            self.target.difference_update(nodeset)
        elif mode is 'INT' and self.target:
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

    def update_status(self, status):
        '''
        Update the current service's status and whether all of his parents
        dependencies are solved start children dependencies.
        '''
        if self.warnings and status is DONE:
            self.status = WARNING
        else:
            self.status = status

        if not self.simulate:
            call_back_self().notify(self, EV_STATUS_CHANGED)

        # I got a status so I'm DONE or DEP_ERROR and I'm not the calling point
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

        # Service with missing action is simply skipped
        elif not self.has_action(self._last_action):
            self.update_status(MISSING)

        else:
            # It's time to be processed
            self.update_status(WAITING_STATUS)
            self._actions[self._last_action].prepare()

    def prepare(self, action_name=None):
        '''
        Prepare the the current service to be launched as soon
        as his dependencies are solved. 
        '''
        if action_name:
            self._last_action = action_name

        deps_status = self.eval_deps_status()
        # Tag the service
        self._tagged = True

        if self.status is NO_STATUS:

            # If dependencies failed the current service will fail
            # except if the service is SKIPPED
            if deps_status == DEP_ERROR and not self.skipped():
                self.update_status(DEP_ERROR)
            else:
                if self.skipped():
                    self.update_status(SKIPPED)
                # Just flag if dependencies encountered problem
                if deps_status == WARNING:
                    self.warnings = True

                # Look for uncompleted dependencies 
                deps = self.search_deps([NO_STATUS])

                # XXX:
                # _process_dependencies() does not only take care or deps,
                # but also launch the service if there is no more deps.
                # Such action should be done, depending on deps_status.
                #
                # As this function does not know yet how to handle this
                # we check this before calling it.
                if deps_status is not WAITING_STATUS or deps:
                    self._process_dependencies(deps)

    def inherits_from(self, entity):
        '''Inherit properties from entity'''
        BaseEntity.inherits_from(self, entity)
        for action in self.iter_actions():
            action.inherits_from(self)

    def fromdict(self, svcdict):
        """Populate service attributes from dict."""
        BaseEntity.fromdict(self, svcdict)

        if 'actions' in svcdict:
            dependencies = {}
            actions = {}
            for names, props in svcdict['actions'].items():
                for name in NodeSet(names):
                    action = Action(name)
                    action.fromdict(props)

                    actions[name] = action
                    dependencies[name] = props.get('check', [])

            for action in actions.values():
                for dep in dependencies[action.name]:
                    action.add_dep(actions[dep])
                self.add_action(action)

        # Inherits properies between service and actions
        for action in self.iter_actions():
            action.inherits_from(self)
