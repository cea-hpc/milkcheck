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
        
        # Flag to certify that an action was delayed
        self.delayed = False
        
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