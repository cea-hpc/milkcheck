# Copyright CEA (2011) 
# Author: Aurelien Degremont <aurelien.degremont@cea.fr>

import os
import yaml

class ConfigParserError(Exception):
    '''Error in configuration file.'''

class ConfigParser(object):

    CONFIG_PATH = '/etc/milkcheck/milkcheck.conf'
    FIELDS = { 
         'config_dir':  { 'value': '/etc/milkcheck/conf', 'type': str } 
         }

    def __init__(self, options):
        
        # Read config files
        if os.access(self.CONFIG_PATH, os.F_OK):
            data = yaml.load(open(self.CONFIG_PATH))
            # Parse read content
            self._check_data(data)

        # Apply command line overrides:
        for element in ('config_dir'):
            if hasattr(options, element):
                self[element] = getattr(options, element)
 
    def _check_data(self, data):
        for element, value in data.iteritems():
            if element not in self.FIELDS:
                raise ConfigParserError("Bad entry '%s'" % element)
            if type(value) is not self.FIELDS[element]['type']:
                raise ConfigParserError("Wrong value '%s' for '%s'" 
                                        % (value, element))
            self[element] = value

    def __getitem__(self, key):
        return self.FIELDS[key]['value']

    def __setitem__(self, key, value):
        self.FIELDS[key]['value'] = value
