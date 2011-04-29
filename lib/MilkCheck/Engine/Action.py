# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This module contains the Action class definition and the defintion
of the different event handlers
"""
# Classes
from datetime import datetime
from ClusterShell.Task import task_self
from ClusterShell.Event import EventHandler
from MilkCheck.Engine.BaseEntity import BaseEntity

# Symbols
from MilkCheck.Engine.BaseService import RUNNING, TIMED_OUT, TOO_MANY_ERRORS
from MilkCheck.Engine.BaseService import RUNNING_WITH_WARNINGS, WAITING_STATUS
from MilkCheck.Engine.BaseService import ERROR

class MilkCheckEventHandler(EventHandler):
    """Defines the basic event handler available for MilkCheck"""
    
    def __init__(self, action, paction_name=None):
        EventHandler.__init__(self)
        assert action, "should not be be None"
        # Current action processed by the handler
        self._action = action
        # Name of parent action
        self._paction_name = paction_name
        
    def ev_timer(self, timer):
        """An action was waiting for the timer"""
        print "[%s] ev_timer" % self._action.parent.name
        self._action.schedule(allow_delay=False)
        print "[%s] delayed action added to the master task" % \
        self._action.parent.name  
       
        
class ActionEventHandler(MilkCheckEventHandler):
    """
    Defines the events used when an action of service is launched within
    the master task
    """
    
    def ev_close(self, worker):
        """An action which was within the master task is done."""
        print datetime.now()
        self._action.duration = datetime.now().second - self._action.duration 
        self._action.worker = worker
        error = self._action.has_too_many_errors()
        timed_out = self._action.has_timed_out()
        
        # Classic Action was failed
        if error or timed_out:
            self._action.status = ERROR
            # Opportunity to retry the current action
            if self._action.retry > 0:
                self._action.retry -= 1
                self._action.schedule()
            # Classic action failed 
            elif not self._action.children:
                if error:
                    self._action.parent.update_status(TOO_MANY_ERRORS)
                elif timed_out:
                    self._action.parent.update_status(TIMED_OUT)
            # Sub Action failed whether it doesn't have dependencies
            # waiting just schedule the parent action
            elif not \
                self._action.children[self._paction_name].has_waiting_deps():
                self._action.children[self._paction_name].schedule()
        # Classic Action was successful 
        elif not self._action.children:
            if self._action.parent.warnings:
                self._action.parent.update_status(RUNNING_WITH_WARNINGS)
            else:
                self._action.parent.update_status(RUNNING)
        # Sub-action was successful
        else:
            stats = self._action.children[self._paction_name].eval_deps_status()
            if stats is RUNNING:
                self._action.parent.update_status(RUNNING)
            elif stats is ERROR:
                self._action.parent.update_status(ERROR)
                
class Action(BaseEntity):
    """
    This class models an action. An action can be applied to a service
    and contain the code that we need to execute on nodes specified in the
    action or service.
    """
    
    def __init__(self, name, target=None, command=None, timeout=0, delay=0):
        BaseEntity.__init__(self, name=name, target=target)
        
        # Action's timeout in seconds
        self.timeout = timeout
        
        # Action's delay in seconds
        self.delay = delay
        
        # Number of action's retry
        self._retry = 0
        
        # Command lines that we would like to run 
        self.command = command
        
        # Results and retcodes
        self.worker = None
        
        # Direct parent object (should be a service)
        self.parent = None
        
        # Duration show up the time used by the CPU for this action
        self.duration = None
        
    def has_timed_out(self):
        """Return whether this action has timed out."""
        return self.worker and self.worker.did_timeout()
        
    def has_too_many_errors(self):
        """
        Return true if the amount of error in the worker is greater than
        the limit authorized by the action.
        """
        too_many_errors = False
        error_count = 0
        if self.worker:
            for retcode, nds in self.worker.iter_retcodes():
                if retcode != 0:
                    error_count += len(nds)
                    if error_count > self.errors:
                        too_many_errors = True
        return too_many_errors
                    
    def set_retry(self, retry):
        """constraint retry property setter"""
        assert self.delay > 0 , "No way to specify retry without a delay"
        self._retry = retry
        
    def get_retry(self):
        """retry property getter"""
        return self._retry
    
    retry = property(fget=get_retry, fset=set_retry) 
    
    def schedule(self, allow_delay=True, paction_name=None):
        """Schedule the current action within the Master Task"""
        task = task_self()
        if self.delay > 0 and allow_delay:
            # Action will be started as soon as the timer is done
            task.timer(handler=ActionEventHandler(self, paction_name),
                fire=self.delay)
            print datetime.now().second
            self.duration = datetime.now().second
            print "[%s] action [%s] delayed" % (self.parent.name, self.name)
        else:
            # Fire this action
            task.shell(self.command,
                nodes=self.target, handler=ActionEventHandler(self, \
                    paction_name), timeout=self.timeout)
            self.status = WAITING_STATUS
            print "[%s] action [%s] in Task " % (self.parent.name, self.name)
            self.duration = datetime.now().second
            
    def eval_deps_status(self, reverse=False):
        """
        Evaluate the status of parent/child dependencies depending
        on the value of the reverse flag
        """ 
        status = RUNNING
        for parent_name in self.parents:
            if self.parents[parent_name].status is WAITING_STATUS:
                return WAITING_STATUS            
            elif self.parents[parent_name].has_too_many_errors() or \
                self.parents[parent_name].timed_out():
                return ERROR
        return status