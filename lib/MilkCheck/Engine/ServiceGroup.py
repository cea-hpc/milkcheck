# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This module contains the ServiceGroup class definition
"""

# Classes
from MilkCheck.Engine.BaseService import BaseService

# Symbols
from MilkCheck.Engine.BaseService import NO_STATUS, SUCCESS
from MilkCheck.Engine.BaseService import IN_PROGRESS, ERROR, TIMED_OUT
from MilkCheck.Engine.BaseService import TOO_MANY_ERRORS, SUCCESS_WITH_WARNINGS
from MilkCheck.Engine.Dependency import CHECK, REQUIRE, REQUIRE_WEAK

# Exceptions
from MilkCheck.Engine.BaseEntity import MilkCheckEngineError 

class ServiceAlreadyReferencedError(MilkCheckEngineError):
    """
    This error is raised if you attempt to add a service to group
    and this service is already referenced in it
    """
    def __init__(self, gname, sname):
        msg = "%s already has subservice named %s"  % (gname, sname)
        MilkCheckEngineError.__init__(self, msg)

class ServiceNotFoundError(MilkCheckEngineError):
    """
    This error is raised if the service that you are looking for is not
    referenced in the group
    """
    def __init__(self, gname, sname):
        msg = "%s cannot be found in %s"  % (sname, gname)
        MilkCheckEngineError.__init__(self, msg)

class ServiceGroup(BaseService):
    """
    This class models a group of service. A group of service
    does not own actions, but subservices which are instances
    of Service or ServiceGroup.
    """
        
    def has_subservice(self, name):
        """
        Check if the service is referenced within the group
        """
        return (name in self._deps and self._deps[name].is_internal())
        
    def search_deps(self, symbols=None):
        """
        Return a dictionnary of dependencies both external and internal.
        In order to be in the dictionnary the dependencies must have one
        of the following status.
        """
        depmap = {}
        depmap["external"] = []
        depmap["internal"] = []
        
        for depname in self._deps:
            if self._deps[depname].target.status in symbols:
                if self._deps[depname].is_internal():
                    depmap["internal"].append(self._deps[depname])
                else:
                    depmap["external"].append(self._deps[depname])
        return depmap
                    
    def prepare(self, action_name=None):
        """
        Prepare the the current group to be launched as soon
        as his dependencies are solved
        """
        # Eval the status of the dependencies
        deps_status = self.eval_deps_status()
        
        # The group has no status and not any dep in progress
        if self.status == NO_STATUS and not deps_status == IN_PROGRESS:
            
            print "[%s] is preparing" % self.name
            
            if deps_status == ERROR:
                # Dependency fail badly so the group fail
                self.update_status(ERROR)
            else:
                # Just flag that dependencies encountered some issues
                if deps_status == SUCCESS_WITH_WARNINGS:
                    self.warnings = True
                
                # Look for deps without status (external and internal)
                deps = self.search_deps([NO_STATUS])

                if deps['external'] or deps['internal']:
                    # First resolve external then internal dependencies
                    for priority in ['external','internal']:
                        for dep in deps[priority]:
                            print "[%s] %s dep of %s" % \
                            (dep.target.name, priority, self.name)
                            if dep.is_check():
                                dep.target.prepare('status')
                            else:
                                dep.target.prepare(action_name)
                else:
                    # The group node is a fake we just change his status
                    self.update_status(SUCCESS)
                
    def ev_hup(self, worker):
        """
        Called to indicate that a worker's connection has been closed.
        """
        pass
        
    def ev_close(self, worker):
        """
        Called to indicate that a worker has just finished (it may already
        have failed on timeout).
        """
        pass