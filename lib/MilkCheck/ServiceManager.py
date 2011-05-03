# Copyright CEA (2011)  
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This module contains the ServiceManager class definition.
"""

# Classes
from ClusterShell.Task import task_self

# Exceptions
from MilkCheck.Engine.BaseEntity import MilkCheckEngineError

class ServiceNotFoundError(MilkCheckEngineError):
    """
    Define an exception raised when you are looking for a service
    that does not exist.
    """
    def __init__(self, message="Service is not referenced by the manager"):
        """Constructor"""
        MilkCheckEngineError.__init__(self, message)

class ServiceManager(object):
    """
    The service manager has to handle call to services. It implements
    features allowing us to get dependencies of service and so on.
    """
    
    class RunningTasksManager(object):
        """
        Maintain a list of tasks running in the master task. It allow
        us to control the fanout
        """
        def __init__(self):
            # Current fanout
            self.fanout = None
            # ClusterShell default value
            self.default_fanout = 64
            # Running tasks
            self._running_tasks = {}
            # Count tasks which worked
            self._tasks_done_count = 0
            # Count tasks which are running
            self._tasks_count = 0
            
        def add_task(self, task):
            """
            Fanout goes down whether it is lower than the current
            fanout. Each time the task is added to right category
            if it already belongs to the category the task is not
            added 
            """
            assert task, 'You cannot add a None task to the manager'
            # Task is not already running
            if not self.is_running_task(task):
                fnt = task.fanout
                # No fanout or invalid value, fanout gets the default value
                if not fnt or fnt < 1:
                    fnt = self.default_fanout
                # Create the category if it does not exist
                if not self._running_tasks.has_key(fnt):
                    self._running_tasks[fnt] = set()
                # New fnt is lower than the current fanout
                if not self.fanout or fnt < self.fanout:
                    task_self().set_info('fanout', fnt)
                    self.fanout = fnt
                # Finally add the task and manage counters
                self._running_tasks[fnt].add(task)
                self._tasks_done_count += 1
                self._tasks_count += 1
            
        def remove_task(self, task):
            """
            Fanout goes up whether the current task represents the lower
            fanout available and not any task owns the same fanout  
            """
            assert task, 'You cannot take out a None task'
            # Task given as parameter is not already running
            if self.is_running_task(task):
                # Checkout the right value for the fanout
                fnt = task.fanout
                if not fnt or fnt < 1:
                    fnt = self.default_fanout
                # Remove task
                self._running_tasks[fnt].remove(task)

                # Category is empty so we delete it and we update
                # the value of the current fanout
                if len(self._running_tasks[fnt]) == 0:
                    del self._running_tasks[fnt]
                    if self._running_tasks:
                        self.fanout = self._running_tasks.keys()[0]
                        task_self().set_info('fanout', self.fanout)
                    else:
                        self.fanout = None
                # Current number of task is decremented
                self._tasks_count -= 1

        def is_running_task(self, task):
            """
            Allow us to determine whether a task is running or not
            """
            assert task, 'Task cannot be None'
            if not task.fanout or task.fanout < 1:
                return self._running_tasks.has_key(self.default_fanout) and \
                    task in self._running_tasks[self.default_fanout]
            return self._running_tasks.has_key(task.fanout) and \
                    task in self._running_tasks[task.fanout]


        @property
        def running_tasks(self): # Retourner iterateur
            """Return an iterator over the running_tasks"""
            return self._running_tasks.itervalues()

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
               
    
    # single instance of the ServiceManager
    _manager = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._manager:
            cls._manager = super(ServiceManager, cls).__new__(
                cls, *args, **kwargs)
        return cls._manager    
    
    def __init__(self):
        # Services handled by the manager
        self._services = {}
        
        # Variables declared in the global scope
        self._variables = {}
        
        # Running tasks manager
        self.rtasks = ServiceManager.RunningTasksManager()
        
    def call_services(self, services_names, action_name, params=None):
        """Allow the user to call one or multiple services."""
        for name in services_names:
            service = None
            normalized_name = name.lower()
            if self._services.has_key(normalized_name):
                service = self._services[normalized_name]
                service.run(action_name)
            else:
                raise ServiceNotFoundError
    
    def dependencies(self, service_name):
        pass