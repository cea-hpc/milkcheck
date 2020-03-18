#
# Copyright CEA (2011-2017)
#
# This file is part of MilkCheck project.
#
# This software is governed by the CeCILL license under French law and
# abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# "http://www.cecill.info".
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and,  more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.

"""
This module contains the Service class definition
"""

# Classes
from ClusterShell.NodeSet import NodeSet
from MilkCheck.Engine.BaseEntity import BaseEntity
from MilkCheck.Engine.Action import Action, action_manager_self
from MilkCheck.Callback import call_back_self

# Exceptions
from MilkCheck.Engine.BaseEntity import MilkCheckEngineError

# Symbols
from MilkCheck.Engine.BaseEntity import NO_STATUS, MISSING, DEP_ERROR
from MilkCheck.Engine.BaseEntity import WAITING_STATUS
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

class Service(BaseEntity):
    '''
    A Service might be a node of graph because it inherits from the properties
    and methods of BaseEntity.
    A Service contains actions, and those actions are called and executed on
    nodes.
    '''

    LOCAL_VARIABLES = BaseEntity.LOCAL_VARIABLES.copy()
    LOCAL_VARIABLES['SERVICE'] = 'name'

    def __init__(self, name, target=None):
        BaseEntity.__init__(self, name, target)

        # Define a flag allowing us to specify that this service is the
        # original caller so we do not have to start his children.
        self.origin = False

        # Used for ghost services or services that you do not want to execute.
        self.simulate = False

        # Actions of the service
        self._actions = {}
        self._last_action = None

    def update_target(self, nodeset, mode=None):
        '''Update the attribute target of a service'''
        BaseEntity.update_target(self, nodeset, mode)
        for action in self._actions.values():
            action.update_target(nodeset, mode)

    def reset(self):
        '''Reset values of attributes in order to perform multiple exec'''
        BaseEntity.reset(self)
        self.origin = False
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
        for key, act in self._actions.items():
            yield act

    def remove_action(self, action_name):
        '''Remove the specified action from those available in the service.'''
        if action_name in self._actions:
            del self._actions[action_name]
        else:
            raise ActionNotFoundError(self.name, action_name)

    def has_action(self, action_name):
        '''Figure out whether the service has the specified action.'''
        return action_name in self._actions

    def skip(self):
        """Skip this service"""
        for action in self.iter_actions():
            action.skip()

    def to_skip(self, action):
        """Tell if service should be skipped for provided action name."""
        return self.has_action(action) and self._actions[action].to_skip()

    def update_status(self, status):
        '''
        Update the current service's status and whether all of his parents
        dependencies are solved start children dependencies.
        '''
        self.status = status

        if not self.simulate:
            call_back_self().notify(self, EV_STATUS_CHANGED)

        # I got a status so I'm DONE or DEP_ERROR and I'm not the calling point
        if self.status not in (NO_STATUS, WAITING_STATUS) and not self.origin:

            # Trigger each service which depend on me as soon as it does not
            # have WAITING_STATUS parents
            deps = self.children
            if self._algo_reversed:
                deps = self.parents

            for dep in deps.values():
                tgt = dep.target

                # Propagate this info, even if 'tgt' will not be run right now
                dep.filter_nodes(self.failed_nodes)

                if tgt.status is NO_STATUS and tgt.is_ready() and tgt._tagged:
                    if not self.simulate:
                        call_back_self().notify((self, tgt), EV_TRIGGER_DEP)
                    tgt.prepare()

    def _launch_action(self, action, status):
        """
        Try to launch the action.

        Service status and deps should be already checked.
        """
        # Service with missing action is simply skipped
        if not self.has_action(action):
            self.update_status(MISSING)
        elif self.to_skip(action):
            # We are sure the action will be set to SKIPPED
            self._actions[action].prepare()
        elif status == DEP_ERROR:
            self.update_status(DEP_ERROR)
        else:
            # It's time to be processed
            self.update_status(WAITING_STATUS)
            self._actions[action].prepare()

    def prepare(self, action_name=None):
        """
        Recursive method allowing to prepare a service before its execution.
        The preparation of a service consists in checking that all of the
        dependencies linked to this service were solved. As soon as possible
        requested action will be started.
        """
        if action_name:
            self._last_action = action_name

        # Add a flag 'i was prepared', used in update_status()
        self._tagged = True

        # Already in a final state: Nothing to do
        if self.status is not NO_STATUS:
            return

        deps_status = self.eval_deps_status()

        # Deps not yet processed: Launch them!
        deps = self.search_deps([NO_STATUS])
        if deps:
            for dep in deps:
                if dep.is_check():
                    dep.target.prepare('status')
                else:
                    dep.target.prepare(self._last_action)
        # No dep still running: Run me
        elif deps_status is not WAITING_STATUS:
            self._launch_action(self._last_action, deps_status)

    def run(self, action_name):
        """Run an action over a service"""
        # A service using run become the calling point
        self.origin = True

        # Prepare the service and start the master task
        self.prepare(action_name)
        action_manager_self().run()

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
            for names, props in svcdict['actions'].items():
                for name in NodeSet(names):
                    action = Action(name)
                    self.add_action(action)
                    action.fromdict(props)

                    dependencies[name] = props.get('check', [])

            for action in self._actions.values():
                for dep in dependencies[action.name]:
                    action.add_dep(self._actions[dep])

        # Inherits properies between service and actions
        for action in self.iter_actions():
            action.inherits_from(self)

    def resolve_all(self):
        """Resolve all variables in Service properties"""
        BaseEntity.resolve_all(self)
        for action in self.iter_actions():
            action.resolve_all()
