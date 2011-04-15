# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This module contains the Action class definition
"""

from MilkCheck.Engine.BaseEntity import BaseEntity

class Action(BaseEntity):
    """
    This class models an action. An action can be applied to a service
    and contain the code that we need to execute on nodes specified in the
    action or service.
    """
    
    def __init__(self, name, target=None, command=None, timeout=0):
        BaseEntity.__init__(self, name=name, target=target)
        
        # Action's timeout in seconds
        self.timeout = timeout
        
        # Action's delay in seconds
        self.delay = 0
        
        # Number of action's retry
        self.retry = 0
        
        # Command lines that we would like to run 
        self.command = command
        
        # Results and retcodes
        self.worker = None
        
    def has_timed_out(self):
        """Return true if this action timed."""
        timed_out = False
        if self.worker:
            timed_out = self.worker.did_timeout()
        return timed_out
        
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