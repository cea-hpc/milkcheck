#
# Copyright CEA (2011-2012)
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
This module contains the Action class definition.

It also contains the definition of a basic event handler and the
ActionEventHandler and ActionManager.
"""

from datetime import datetime

from ClusterShell.Worker.Popen import WorkerPopen
from ClusterShell.Event import EventHandler
from ClusterShell.NodeSet import NodeSet
from ClusterShell.Task import task_self

from MilkCheck.Callback import call_back_self
from MilkCheck.EntityManager import EntityManager
from MilkCheck.Engine.BaseEntity import BaseEntity
from MilkCheck.Engine.BaseEntity import DONE, TIMEOUT, ERROR, WAITING_STATUS, \
                                        NO_STATUS, DEP_ERROR, SKIPPED, WARNING
from MilkCheck.Callback import EV_COMPLETE, EV_STARTED, EV_TRIGGER_DEP, \
                               EV_STATUS_CHANGED, EV_DELAYED, EV_FINISHED


class ActionManager(EntityManager):
    """
    The action manager handle the evolution of the fanout through the current
    running tasks. It provides two methods which allow the user to use
    Action objects to perform task.This class is the only one where
    clustershell is called
    """

    def __init__(self):
        EntityManager.__init__(self)
        # Current fanout
        self.fanout = None
        # ClusterShell default value
        self.default_fanout = 64
        # Count tasks which worked
        self._tasks_done_count = 0
        # Count tasks which are running
        self._tasks_count = 0
        # MasterTask
        self._master_task = task_self()

        self.dryrun = False

    def perform_action(self, action):
        """Perform an immediate action"""
        assert not action.to_skip(), "Action should be already SKIPPED"

        if not action.parent.simulate:
            self.add_task(action)
        call_back_self().notify(action.parent, EV_STARTED)

        nodes = None
        if action.mode != 'delegate':
            nodes = action.target

        # In dry-run mode, all commands are replaced by a simple ':'
        command = ':'
        if not self.dryrun:
            command = action.resolve_property('command')

        self._master_task.shell(command, nodes=nodes, timeout=action.timeout,
                                handler=ActionEventHandler(action))

    def perform_delayed_action(self, action):
        """Perform a delayed action and add it to the running tasks"""
        assert action, 'You cannot perform a NoneType object'
        assert isinstance(action, Action), 'Object should be an action'
        if not action.parent.simulate:
            self.add_task(action)
            call_back_self().notify(action, EV_DELAYED)
        self._master_task.timer(handler=ActionEventHandler(action),
                                fire=action.delay)

    def add_task(self, task):
        """
        Fanout goes down whether it is lower than the current
        fanout. Each time the task is added to right category
        if it already belongs to the category the task is not
        added
        """
        assert task, 'You cannot add a None task to the manager'
        # Task is not already running
        if not self._is_running_task(task):
            fnt = task.fanout
            # No fanout or invalid value, fanout gets the default value
            if not fnt or fnt < 1:
                fnt = self.default_fanout
            # Create the category if it does not exist
            if not self.entities.has_key(fnt):
                self.entities[fnt] = set()
            # New fnt is lower than the current fanout
            if not self.fanout or fnt < self.fanout:
                self._master_task.set_info('fanout', fnt)
                self.fanout = fnt
            # Finally add the task and manage counters
            self.entities[fnt].add(task)
            self._tasks_done_count += 1
            self._tasks_count += 1

    def remove_task(self, task):
        """
        Fanout goes up whether the current task represents the lower
        fanout available and not any task owns the same fanout
        """
        assert task, 'You cannot take out a None task'
        # Task given as parameter is not already running
        if self._is_running_task(task):
            # Checkout the right value for the fanout
            fnt = task.fanout
            if not fnt or fnt < 1:
                fnt = self.default_fanout
            # Remove task
            self.entities[fnt].remove(task)
            call_back_self().notify(task.parent, EV_COMPLETE)

            # Category is empty so we delete it and we update
            # the value of the current fanout
            if len(self.entities[fnt]) == 0:
                del self.entities[fnt]
                if self.entities:
                    self.fanout = self.entities.keys()[0]
                    self._master_task.set_info('fanout', self.fanout)
                else:
                    self.fanout = None
            # Current number of task is decremented
            self._tasks_count -= 1
        if not self.tasks_count:
            call_back_self().notify(task.parent, EV_FINISHED)

    def _is_running_task(self, task):
        """
        Allow us to determine whether a task is running or not
        """
        assert task, 'Task cannot be None'
        if not task.fanout or task.fanout < 1:
            return self.entities.has_key(self.default_fanout) and \
                task in self.entities[self.default_fanout]
        return self.entities.has_key(task.fanout) and \
                task in self.entities[task.fanout]

    def run(self):
        """ Run the action manager task"""
        if not self._master_task.running():
            self._master_task.run()

    @property
    def running_tasks(self):
        """Return a set of running tasks"""
        running_tasks = set()
        for tasks in self.entities.values():
            running_tasks.update(tasks)
        return running_tasks

    @property
    def tasks_count(self):
        """
        Make the property read only and returns the current number of
        tasks running
        """
        return self._tasks_count

    @property
    def tasks_done_count(self):
        """
        Make the property read only and returns the number of
        tasks which ran within the manager
        """
        return self._tasks_done_count

def action_manager_self():
    """Return a singleton instance of the ActionManager class"""
    if not ActionManager._instance:
        ActionManager._instance = ActionManager()
    return ActionManager._instance


class MilkCheckEventHandler(EventHandler):
    '''
    The basic event handler for MilkCheck derives the class provided
    by ClusterShell to handle events generated by the master task. It contains
    an action as attribute. This action is the element processed through the
    events raised. 
    '''
    
    def __init__(self, action):
        EventHandler.__init__(self)
        assert action, "should not be be None"
        # Current action hooked to the handler
        self._action = action

    def ev_start(self, worker):
        '''Command has been started on a nodeset'''
        if not self._action.parent.simulate:
            call_back_self().notify(self._action, EV_STARTED)

    def ev_timer(self, timer):
        '''
        A timer event is raised when an action was delayed. Now the timer is
        done so we can really execute the action. This method is also used
        to handle action with a service which is specified as ghost. That means
        it does nothing
        '''
        self._action.schedule(allow_delay=False)
       
        
class ActionEventHandler(MilkCheckEventHandler):
    '''
    Inherit from our basic handler and specify others event raised to
    process an action.
    '''
    
    def ev_hup(self, worker):
        '''Update remaining target'''
        self._action.pending_target.remove(worker.current_node)

    def ev_close(self, worker):
        '''
        This event is raised by the master task as soon as an action is
        done. It specifies the how the action will be computed.
        '''
        # Assign time duration to the current action
        self._action.stop_time = datetime.now()

        # Remove the current action from the running task, this will trigger
        # a redefinition of the current fanout
        action_manager_self().remove_task(self._action)

        # Get back the worker from ClusterShell
        self._action.worker = worker

        # Checkout actions issues
        errors = self._action.nb_errors()
        timeouts = self._action.nb_timeout()
        failed = errors + timeouts

        # Classic Action was failed
        if failed and self._action.tries <= self._action.maxretry:
            self._action.schedule()

        # timeout when more timeouts than permited
        elif timeouts > self._action.errors and errors == 0:
            self._action.update_status(TIMEOUT)
        # _action.errors has a higher priority than _action.warnings
        # failed when too many errors
        elif failed > self._action.errors:
            self._action.update_status(ERROR)
        # Warning if there is more failed actions than the warning threshold
        elif failed > self._action.warnings:
            self._action.update_status(WARNING)
        else:
            self._action.update_status(DONE)

class Action(BaseEntity):
    '''
    This class models an action. An action is generally hooked to a service
    and contains the code and parameters to execute commands over one or several
    nodes of a cluster. An action might have dependencies with other actions.
    '''

    LOCAL_VARIABLES = BaseEntity.LOCAL_VARIABLES.copy()
    LOCAL_VARIABLES['ACTION'] = 'name'
    
    def __init__(self, name, target=None, command=None, timeout=-1, delay=0):
        BaseEntity.__init__(self, name=name, target=target, delay=delay)
        
        # Action's timeout in seconds/milliseconds
        self.timeout = timeout
        
        # Number of action tries
        self.tries = 0
        
        # Command lines that we would like to run 
        self.command = command
        
        # Results and retcodes
        self.worker = None
        
        # Allow us to determine time used by an action within the master task
        self.start_time = None
        self.stop_time = None

        # Store pending targets
        self.pending_target = NodeSet()

    def reset(self):
        '''
        Reset values of attributes in order to used the action multiple time.
        '''
        BaseEntity.reset(self)
        self.start_time = None
        self.stop_time = None
        self.worker = None
        self.tries = 0

    def run(self):
        '''Prepare the current action and set up the master task'''
        self.prepare()
        action_manager_self().run()

    def to_skip(self):
        """Tell if action has an empty target list and should be skipped."""
        return (self.target != None and len(self.target) == 0)

    def prepare(self):
        '''
        Prepare is a recursive method allowing the current action to prepare
        actions which are in dependency with her first. An action can only
        be prepared whether the dependencies are not currently running and if
        the current action has not already a status.
        '''
        deps_status = self.eval_deps_status()
        # NO_STATUS and not any dep in progress for the current action
        if self.status is NO_STATUS and deps_status is not WAITING_STATUS:
            if self.to_skip():
                self.update_status(SKIPPED)
            elif deps_status is DEP_ERROR or not self.parents:
                self.update_status(WAITING_STATUS)
                self.schedule()
            elif deps_status is DONE:
                # No need to do the action so just make it DONE
                self.update_status(DONE)
            else:
                # Look for uncompleted dependencies
                deps = self.search_deps([NO_STATUS])
                # For each existing deps just prepare it
                for dep in deps:
                    dep.target.prepare()
                    
    def update_status(self, status):
        '''
        This method update the current status of an action. Whether the
        a status meaning that the action is done is specified, the current
        action triggers her direct dependencies.
        '''
        self.status = status
        call_back_self().notify(self, EV_STATUS_CHANGED)
        if status not in (NO_STATUS, WAITING_STATUS):
            if not self.parent.simulate:
                call_back_self().notify(self, EV_COMPLETE)
            if self.children:
                for dep in self.children.values():
                    if dep.target.is_ready():
                        if not self.parent.simulate:
                            call_back_self().notify(
                            (self, dep.target), EV_TRIGGER_DEP)
                        dep.target.prepare()
            else:
                self.parent.update_status(self.status)
        
    def nb_timeout(self):
        '''Return the number of timeout runs.'''
        if self.worker:
            if isinstance(self.worker, WorkerPopen):
                if self.worker.did_timeout():
                    return 1
            else:
                return len(list(self.worker.iter_keys_timeout()))
        return 0
        
    def nb_errors(self):
        '''
        Return the amount of error in the worker.
        '''
        error_count = 0
        if self.worker:
            if isinstance(self.worker, WorkerPopen):
                retcode = self.worker.retcode()
                # We don't count timeout (retcode=None)
                if retcode not in (None, 0):
                    error_count = 1
            else:
                for retcode, nds in self.worker.iter_retcodes():
                    if retcode != 0:
                        error_count += len(nds)
        return error_count
                    
    @property
    def duration(self):
        '''
        Task duration in seconds (10^-6) is readable as soon as the task is done
        otherwise it returns None.
        '''
        if not self.start_time or not self.stop_time:
            return None
        else:
            delta = self.stop_time - self.start_time
            return  delta.seconds + (delta.microseconds/1000000.0)

    
    def schedule(self, allow_delay=True):
        '''
        Schedule the current action within the master task. The current action
        could be delayed or fired right now depending of it properties.
        '''
        if not self.start_time:
            self.start_time = datetime.now()

        self.pending_target.add(self.target)

        if self.delay > 0 and allow_delay:
            # Action will be started as soon as the timer is done
            action_manager_self().perform_delayed_action(self)
        else:
            # Fire this action
            self.tries += 1
            action_manager_self().perform_action(self)

    def fromdict(self, actdict):
        """Populate action attributes from dict."""
        BaseEntity.fromdict(self, actdict)

        if 'cmd' in actdict:
            self.command = actdict['cmd']
