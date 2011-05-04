# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This module contains the ServiceGroup class definition
"""

# Classes
from MilkCheck.Engine.Service import Service
from MilkCheck.Engine.BaseEntity import BaseEntity

# Symbols
from MilkCheck.Engine.Dependency import REQUIRE
from MilkCheck.Engine.BaseEntity import NO_STATUS, DONE
from MilkCheck.Engine.BaseEntity import WAITING_STATUS, ERROR
from MilkCheck.Engine.BaseEntity import DONE_WITH_WARNINGS

class ServiceGroup(Service):
    """
    This class models a group of service. A group of service
    can own actions it's no mandatory. However it shall have
    subservices
    """

    def __init__(self):
        Service.__init__(self)
        # Entry point of the group
        self._entry = Service('entry')
        # 
        
    def has_subservice(self, name):
        """
        Check if the service is referenced within the group
        """
        return (name in self.parents and self.parents[name].is_internal())
    
    def add_dep(self, target, sgth=REQUIRE, parent=True, inter=False):
        """Overrides the behaviour imposed by Service"""
        BaseEntity.add_dep(self, target, sgth, parent, inter)
    
    def search_deps(self, symbols=None, reverse=False):
        """
        Return a dictionnary of dependencies both external and internal.
        In order to be in the dictionnary the dependencies must have one
        of the following status.
        """
        depmap = {}
        depmap["external"] = []
        depmap["internal"] = []
        
        for depname in self.parents:
            if self.parents[depname].target.status in symbols:
                if self.parents[depname].is_internal():
                    depmap["internal"].append(self.parents[depname])
                else:
                    depmap["external"].append(self.parents[depname])
        return depmap
                    
    def prepare(self, action_name=None, reverse=False):
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
        if self.status == NO_STATUS and not deps_status == WAITING_STATUS:
            
            print "[%s] is working" % self.name
            
            if deps_status == ERROR:
                # Dependency fail badly so the group fail
                self.update_status(ERROR)
            else:
                # Just flag that dependencies encountered some issues
                if deps_status == DONE_WITH_WARNINGS:
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
                        self.update_status(DONE_WITH_WARNINGS)
                    else:
                        self.update_status(DONE)
                        
            print "[%s] end prepare" % self.name