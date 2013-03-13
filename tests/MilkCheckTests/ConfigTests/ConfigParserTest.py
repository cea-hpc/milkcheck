# Copyright CEA (2011-2012)
# Contributors:
#  Aurelien Cedeyn <aurelien.cedeyn@cea.fr>
#

import logging
from unittest import TestCase
from optparse import Values

from MilkCheck.Config.ConfigParser import ConfigParser, ConfigParserError

class MockConfigParser(ConfigParser):
    '''Class to overwrite CONFIGPATH and avoid logging setup'''
    CONFIG_PATH = '/nowhere'
    @staticmethod
    def install_logger(verbose=0, debug=False):
        '''Return a silent logger'''
        return logging.getLogger('milkcheck')

class ConfigParserTest(TestCase):
    '''Define the test cases of the class ConfigParser'''
    def setUp(self):
        '''Setup empty options'''
        self._options = Values()
        setattr(self._options, 'verbosity', 0)
        setattr(self._options, 'debug', False)

    def test_instanciation(self):
        '''Try to instanciate an object of the class ConfigParser'''
        self.assertTrue(MockConfigParser(self._options))

    def test_no_configuration_file(self):
        '''Test if can not access to the configuration file'''
        config = MockConfigParser(self._options)
        for key in ConfigParser.DEFAULT_FIELDS.iterkeys():
            self.assertEqual(config[key], ConfigParser.DEFAULT_FIELDS[key]['value'])

    def test_check_data(self):
        """YAML flow is correctly parsed"""
        config = MockConfigParser(self._options)
        config._check_data({'fanout': 27})
        self.assertEqual(config['fanout'], 27)

    def test_check_data_type(self):
        """Option type is correctly checked"""
        config = MockConfigParser(self._options)
        # Element does not exist
        self.assertRaises(ConfigParserError,
                          config._check_data, {'sugar': 'yes'})
        # Element has a bad type
        self.assertRaises(ConfigParserError,
                          config._check_data, {'fanout': [ 27, 28 ]})
