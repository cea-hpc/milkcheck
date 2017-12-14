# Copyright CEA (2011-2012)
# Contributors:
#  Aurelien Cedeyn <aurelien.cedeyn@cea.fr>
#

import logging
from unittest import TestCase
from optparse import Values
from tempfile import NamedTemporaryFile

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
            self.assertEqual(type(config[key]), ConfigParser.DEFAULT_FIELDS[key]['type'])

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

    def test_check_data_allowed_values(self):
        """Option value is correctly checked"""
        config = MockConfigParser(self._options)
        # Value is not allowed
        self.assertRaises(ConfigParserError,
                          config._check_data, {'report': 'invalid'})
        # Allowed value for report
        for value in ('full', 'no', 'default'):
            config._check_data({'report': value})
            self.assertEqual(config['report'], value)

    def test_check_summary_compat(self):
        """Check compat with summary"""
        setattr(self._options, 'summary', True)
        config = MockConfigParser(self._options)
        self.assertEqual(config['report'], 'default')

        setattr(self._options, 'summary', False)
        config = MockConfigParser(self._options)
        self.assertEqual(config['report'],
                         ConfigParser.DEFAULT_FIELDS['report']['value'])

        setattr(self._options, 'summary', True)
        setattr(self._options, 'report', 'full')
        config = MockConfigParser(self._options)
        self.assertEqual(config['report'], 'full')

    def test_parsing_sample_configuration(self):
        """Parse sample configuration file"""
        class MockLocalConfigParser(MockConfigParser):
            CONFIG_PATH = '../conf/milkcheck.conf'

        config = MockLocalConfigParser(self._options)
        self.assertEqual(config['report'], 'no')
        self.assertEqual(config['fanout'], 64)
        self.assertEqual(config['config_dir'], '/etc/milkcheck/conf')
        self.assertEqual(config['reverse_actions'], ['stop'])

    def test_parsing_summary(self):
        """Parse configuration file with summary option (compat)"""
        tmpfile = NamedTemporaryFile()
        tmpfile.write("summary: True\n")
        tmpfile.flush()

        class MockSummaryLocalConfigParser(MockConfigParser):
            CONFIG_PATH = tmpfile.name
        config = MockSummaryLocalConfigParser(self._options)
        self.assertEqual(config['summary'], True)
