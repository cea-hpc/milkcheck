# Copyright CEA (2011-2012)
# Contributors:
#  Aurelien Degremont <aurelien.degremont@cea.fr>
#  Aurelien Cedeyn <aurelien.cedeyn@cea.fr>
#

'''
This module contains the Configuration parsing management.
'''

import os
import yaml
import logging

class ConfigParserError(Exception):
    '''Error in configuration file.'''

class ConfigParser(object):
    '''
    Contains all Milkcheck configuration
    '''

    CONFIG_PATH = '/etc/milkcheck/milkcheck.conf'
    DEFAULT_FIELDS = {
         'config_dir':  { 'value': '/etc/milkcheck/conf', 'type': str },
         'fanout':      { 'value': '64', 'type': int },
         'summary':     { 'value': False, 'type': bool },
         }

    def __init__(self, options):
        '''
        Parse configuration file and overrides values with the given options
        options: OptionParser.parse_args() returned options object
        '''
        self.fields = dict(self.DEFAULT_FIELDS)

        # Logging configuration
        self.logger = self.install_logger(options.verbosity, options.debug)

        # Read config files
        if os.access(self.CONFIG_PATH, os.F_OK):
            data = yaml.load(open(self.CONFIG_PATH))
            # Parse read content
            self._check_data(data)
        else:
            self.logger.warning("Configuration file %s not found"
                                                           % self.CONFIG_PATH)

        # Apply command line overrides:
        self.update_options(options)

        # Debug mode shows the configuration
        self.logger.debug("Configuration\n%s" % self)

    def update_options(self, options):
        '''
        Update current configuration with the given options
        '''
        # Apply options overrides:
        for opt, value in vars(options).items():
            if value:
                self[opt] = value

    def _check_data(self, data):
        '''
        Check if the option set in the configuration file is allowed to be
        overridden.
        '''
        if data:
            for element, value in data.iteritems():
                if element not in self.fields:
                    raise ConfigParserError("Bad entry '%s'" % element)
                if type(value) is not self.fields[element]['type']:
                    raise ConfigParserError("Wrong value '%s' for '%s'"
                                            % (value, element))
                self[element] = value

    def __getitem__(self, key):
        return self.fields[key]['value']

    def __setitem__(self, key, value):
        self.fields[key] = { 'value' : value, 'type' : type(value) }

    @staticmethod
    def install_logger(verbose=0, debug=False):
        '''Install the various logging methods.'''
        loglvl = [ logging.CRITICAL,
                   logging.ERROR,
                   logging.WARNING,
                   logging.INFO,
                   logging.DEBUG ]

        # create logger
        logger = logging.getLogger('milkcheck')

        # create console handler and set level to debug
        console = logging.StreamHandler()

        # create formatter
        formatter = logging.Formatter(
                         '[%(asctime)s] %(levelname)-8s - %(message)s',
                         datefmt="%H:%M:%S")

        # add formatter to console
        console.setFormatter(formatter)

        # set log level
        if verbose >= len(loglvl) or debug:
            verbose = len(loglvl) - 1
        logger.setLevel(loglvl[verbose])
        console.setLevel(loglvl[verbose])

        # add console to logger
        logger.addHandler(console)

        return logger

    def get(self, key, default = None):
        ''' Helper to get an option from the configuration '''
        try:
            return self.fields[key].get('value', default)
        except KeyError:
            return default

    def __str__(self):
        return "\n".join(["%s: %s" % (opt, self[opt]) for opt in self.fields])
