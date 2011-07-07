# Copyright CEA (2011)
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This module contains the ActionManager class definition.
"""

# Classes
from ClusterShell.Task import task_self
from MilkCheck.EntityManager import EntityManager
from MilkCheck.Engine.Action import Action
from MilkCheck.Engine.Action import ActionEventHandler
from MilkCheck.Callback import call_back_self

# Symbols
from MilkCheck.Callback import EV_STARTED, EV_COMPLETE, EV_DELAYED

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

    def perform_action(self, action):
        """Perform an immediate action"""
        assert action, 'You cannot perform a NoneType object'
        assert isinstance(action, Action), 'Object should be an action'
        if not action.parent.simulate:
            self.add_task(action)
        call_back_self().notify(action.parent, EV_STARTED)
        self._master_task.shell(action.resolve_property('command'),
        nodes=action.resolve_property('target'),
        handler=ActionEventHandler(action), timeout=action.timeout)

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