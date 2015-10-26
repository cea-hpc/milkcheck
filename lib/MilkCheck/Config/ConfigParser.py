#
# Copyright CEA (2011-2012)
#
# Contributors:
#  Aurelien Degremont <aurelien.degremont@cea.fr>
#  Aurelien Cedeyn <aurelien.cedeyn@cea.fr>
#
# This file is part of MilkCheck project.
#
# This software is governed by the CeCILL license under French law and
# abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# "http://www.cecill.info".
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and,  more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.

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
         'config_dir':      { 'value': '/etc/milkcheck/conf', 'type': str },
         'fanout':          { 'value': 64, 'type': int },
         'reverse_actions': { 'value': ['stop'], 'type': list },
         'report':          { 'value': 'no', 'type': str,
                              'allowed_values': ('no', 'default', 'full') },
         }

    def __init__(self, options):
        '''
        Parse configuration file and overrides values with the given options
        options: OptionParser.parse_args() returned options object
        '''
        self.fields = dict(self.DEFAULT_FIELDS)

        # Logging configuration
        self.logger = self.install_logger(options.verbosity)

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
        """
        Update current configuration with the given options
        """
        # Compat code to translate 'summary' to 'report':
        # If 'summary' is present, 'report' will be set to 'default'
        # unless it was previously defined with a different value.
        opt_dict = vars(options)
        if opt_dict.get('summary') and not opt_dict.get('report'):
            self['report'] = 'default'
            del opt_dict['summary']
        # End of compat.

        # Apply options overrides:
        for opt, value in opt_dict.items():
            if value is not None:
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
                if self.fields[element].get('allowed_values') and \
                       value not in self.fields[element]['allowed_values']:
                    raise ConfigParserError("Value for '%s' should be one of %s"
                                        " (found '%s')" % (
                                        element,
                                        self.fields[element]['allowed_values'],
                                        value))
                self[element] = value

    def __getitem__(self, key):
        return self.fields[key]['value']

    def __setitem__(self, key, value):
        self.fields[key] = { 'value' : value, 'type' : type(value) }

    @staticmethod
    def install_logger(verbose=0):
        '''Install the various logging methods.'''
        loglvl = [ logging.CRITICAL,
                   logging.ERROR,
                   logging.WARNING,
                   logging.INFO,
                   logging.DEBUG ]

        # create logger
        logger = logging.getLogger('milkcheck')

        # create console handler
        console = logging.StreamHandler()

        # create formatter
        formatter = logging.Formatter(
                         '[%(asctime)s] %(levelname)-8s - %(message)s',
                         datefmt="%H:%M:%S")

        # add formatter to console
        console.setFormatter(formatter)

        # set log level
        if verbose >= len(loglvl):
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
