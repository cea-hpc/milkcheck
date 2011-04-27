# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This module contains the ServiceGroup class definition
"""

# Classes
from MilkCheck.Engine.BaseService import BaseService

# Symbols
from MilkCheck.Engine.BaseService import NO_STATUS, SUCCESS
from MilkCheck.Engine.BaseService import IN_PROGRESS, ERROR
from MilkCheck.Engine.BaseService import SUCCESS_WITH_WARNINGS

# Exceptions
from MilkCheck.Engine.BaseEntity import MilkCheckEngineError 

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
        
        # Remember last action called
        if action_name:
            self._last_action = action_name
        
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
                    # Before to start internal dependencies we have to be sure
                    # that all external dependencies are solve
                    if deps['external']:
                        for external in deps['external']:
                            print "[%s] external dep of %s" % \
                            (external.target.name, self.name)
                            if external.is_check():
                                external.target.prepare('status')
                            else:
                                external.target.prepare(self._last_action)
                    elif deps['internal']:
                        for internal in deps['internal']:
                            print "[%s] internal dep of %s" % \
                            (internal.target.name, self.name)
                            if internal.is_check():
                                internal.target.prepare('status')
                            else:
                                internal.target.prepare(self._last_action)
                else:
                    # The group node is a fake we just change his status
                    if self.warnings:
                        self.update_status(SUCCESS_WITH_WARNINGS)
                    else:
                        self.update_status(SUCCESS)