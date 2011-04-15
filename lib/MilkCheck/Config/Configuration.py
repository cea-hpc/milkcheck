# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This module contains the
"""

from yaml import load_all
from os.path import walk
from os.path import isfile
from re import match
from MilkCheck.Engine.ServiceFactory import ServiceFactory

class Configuration(object):
    """
    This class reads the configuration files specified in base and override
    directories.
    """
    def __init__(self):
        self._syn_rules_service = {}
        self._syn_rules_action = {}
        self._filepath_base = "../conf/base/"
        self._config = {}

    def _go_through(self, arg, dirname=None, names=None):
        """List the files in dirname"""
        for my_file in names:
            
            if isfile(self._filepath_base + my_file) and \
            match("^[a-zA-Z]*\.yaml$",my_file):
                print "In file : %s" % self._filepath_base + my_file
                yamlfile = open(self._filepath_base + my_file)
                
                for service in load_all(yamlfile):
                    if service is not None:
                        print "%s...[loaded]" % service["service"]["name"]
                        self._config[service["service"]["name"]] = \
                        service["service"]

    def build_config(self):
        """Build and return a list of services objects"""
        self.read_config()
        self.compile_config()
        services = {}
        
        for name in self._config.keys():
            if "services" in self._config[name].keys():
                print "Create service group named %s" % name
            else:
                print "Create service named %s" % name
                
    def compile_config(self):
        """Check the content of the services loaded"""
        print "Compiling configuration"
        return True
    
    def read_config(self):
        """Load the files located in base and override directories"""
        print "Loading Configuration"
        walk(self._filepath_base, self._go_through, None)
        return True