# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This module contains the definition of the different handlers used by
the action class
"""

# Classes
from ClusterShell.Event import EventHandler
from ClusterShell.Task import task_self

# Symbols
from MilkCheck.Engine.BaseService import SUCCESS, TIMED_OUT, TOO_MANY_ERRORS
from MilkCheck.Engine.BaseService import SUCCESS_WITH_WARNINGS

class MilkCheckEventHandler(EventHandler):
    """Defines the basic event handler available for MilkCheck"""
    
    def __init__(self, action):
        EventHandler.__init__(self)
        assert action, "should not be be None"
        self._action = action
       
        
class ActionEventHandler(MilkCheckEventHandler):
    """
    Defines the events used when an action of service is launched within
    the master task
    """
    
    def ev_close(self, worker):
        """An action which was within the master task is done."""
        self._action.worker = worker
        
        # This action has too many errors, so if you can retry it
        # it will be re-scheduled in the master task. Otherwise the
        # status of current service is TOO_MANY_ERRORS
        if self._action.has_too_many_errors():
            if self._action.retry > 0:
                self._action.retry -= 1
                task = task_self()
                task.timer(handler=ActionEventHandler(self._action),
                        fire=self._action.delay)
                print "[%s] is re-scheduled" % self._action.parent.name
            else:
                self._action.parent.update_status(TOO_MANY_ERRORS)
        else:
            # An actions is TIMED_OUT. If you can re-scheduled it, it will
            # go through the master task again. Otherwise the current service
            # is TIMED_OUT
            if self._action.has_timed_out():
                if self._action.retry > 0:
                    self._action.retry -= 1
                    task = task_self()
                    task.timer(
                        handler=ActionEventHandler(self._action),
                            fire=self._action.delay)
                    print "[%s] is re-scheduled" % self._action.parent.name
                else:
                    self._action.parent.update_status(TIMED_OUT)
            else:
                # Action is SUCCESS but parent's dependency could have
                # encountered problems
                if self._action.parent.warnings:
                    self._action.parent.update_status(SUCCESS_WITH_WARNINGS)
                else:
                    self._action.parent.update_status(SUCCESS)
    
    def ev_timer(self, timer):
        """An action was waiting for the timer"""
        print "[%s] ev_timer" % self._action.parent.name
        self._action.delayed = True
        task = task_self()
        task.shell(self._action.command,
            nodes=self._action.target, handler=ActionEventHandler(self._action),
                timeout=self._action.timeout)
        print "[%s] delayed action added to the master task" % self._action.name
        
class SubActionEventHandler(MilkCheckEventHandler):
    """
    Defines the event handler used to take care of the resolution of an
    action fired by another action
    """
    
    def __init__(self, base_action, sub_action):
        MilkCheckEventHandler.__init__(self, base_action)
        assert base_action, "should not be be None"
        self._sub_action = sub_action
    
    def ev_close(self, worker):
        """Sub Action is done"""
        self._sub_action.worker = worker
        
        # The sub action was successul so we needn't to perform
        # the main action
        if not self._sub_action.has_too_many_errors() and \
            not self._sub_action.has_timed_out():
            self._action.parent.update_status(SUCCESS)
        else:
            # The sub action can be retried
            if self._sub_action.retry > 0:
                self._sub_action.retry -= 1
                task = task_self()
                task.timer(
                  handler=SubActionEventHandler(self._action, self._sub_action),
                        fire=self._sub_action.delay)
                print "[%s] [%s] sub-action [%s] re-scheduled" % \
                (self._action.parent.name, self._sub_action.name,
                    sefl._action.name)
            # We need to use the main action because sub action failed
            else:
                task = task_self()
                task.shell(self._action.command,
                    nodes=self._action.target,
                        handler=ActionEventHandler(self._action),
                            timeout=self._action.timeout)        
                print "[%s] action [%s] in Task" % \
                (self._action.parent.name, self._action.name)
                
    def ev_timer(self, timer):
        """An action was waiting for the timer"""
        print "[%s] ev_timer sub_action" % self._sub_action.parent.name
        self._sub_action.delayed = True
        task = task_self()
        task.shell(self._sub_action.command,
            nodes=self._sub_action.target,
                handler=SubActionEventHandler(self._action, self._sub_action),
                timeout=self._sub_action.timeout)
        print "[%s] delayed sub_action added to the master task" % \
        self._action.name    