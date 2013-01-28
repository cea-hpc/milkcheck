# Copyright CEA (2011)
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

'''
This module contains the definition of the OptionParser for MilkCheck.
'''

from optparse import OptionParser, OptionGroup, Option
from copy import copy
from os.path import isdir
from ClusterShell.NodeSet import NodeSet, NodeSetException
import MilkCheck


class InvalidOptionError(Exception):
    '''Exception raised when the parser ran against an unexpected option.'''
    pass

def check_nodeset(_option, _opt, _value):
    '''Try to build a nodeset from the option value.'''
    try:
        return NodeSet(_value)
    except NodeSetException:
        raise InvalidOptionError('%s is not a valid nodeset' % _value)


class MilkCheckOption(Option):
    '''
    This class provide a new type that can be used in the type
    category of the parser.
    '''
    TYPES = Option.TYPES + ('nodeset',)
    TYPE_CHECKER = copy(Option.TYPE_CHECKER)
    TYPE_CHECKER['nodeset'] = check_nodeset

class McOptionParser(OptionParser):
    '''
    Define the parser used to interpret command lines provided by the user.
    This parser owns the default MilkCheck options configuration. Moreover
    it defines the constraints and types checking for the options.
    '''

    def __init__(self, usage=None, option_class=MilkCheckOption, **kwargs):
        version = "%%prog %s" % MilkCheck.__version__
        usage = "usage: %prog [options] [SERVICE...] ACTION"
        OptionParser.__init__(self, usage, version=version,
                              option_class=option_class, **kwargs)

    def configure_mop(self):
        '''Populate the parser with the specified options.'''
        # Display options
        self.add_option('-v', '--verbose', action='count', dest='verbosity',
                        default=1, help='Increase or decrease verbosity')

        self.add_option('-d', '--debug', action='callback',
                        callback=self.__config_debug, dest='debug',
                        help='Set debug mode and maximum verbosity')

        self.add_option('-g', '--graph', action='store_true',
                        dest='graph',
                        help='Output dependencies graph')

        self.add_option('-s', '--summary', action='store_true',
                        dest='summary',
                        help='Display summary of executed actions')

        # Configuration options
        self.add_option('-c', '--config-dir', action='callback',
                        callback=self.__check_dir, type='string',
                        dest='config_dir',
                        help='Change configuration files directory')

        self.add_option('-q', '--quiet', action='store_const', dest='verbosity',
                        const=0, help='Enable quiet mode')

        # Engine options
        eng = OptionGroup(self, 'Engine parameters',
            'Those options allow you to configure the behaviour of the engine')

        eng.add_option('-n', '--only-nodes', action='callback',
                 callback=self.__check_service_mode, type='nodeset',
                 dest='only_nodes',
                 help='Use only the specified nodes')

        eng.add_option('-x', '--exclude-nodes', action='callback',
                 callback=self.__check_service_mode, type='nodeset',
                 dest='excluded_nodes',
                 help='Exclude the cluster\'s nodes specified')

        eng.add_option('-X', '--exclude-service', action='append',
                 dest='excluded_svc', help='Skip the specified services')

        eng.add_option('--dry-run', action='store_true',
                       dest='dryrun', default=False,
                       help='Only simulate command execution')

        self.add_option_group(eng)

    def error(self, msg):
        '''Raise an exception when the parser gets an error.'''
        raise InvalidOptionError(' %s' % msg)

    def __config_debug(self, _option, _opt, _value, _parser):
        '''Configure the debug mode when the parser gets the option -d.'''
        self.values.verbosity = 5
        self.values.debug = True

    def __check_dir(self, _option, _opt, _value, _parser):
        '''Check the content of the option -c'''
        if _value and isdir(_value):
            setattr(self.values, _option.dest, _value)
        else:
            self.error('-c/--config-dir should be a valid directory')

    def __check_service_mode(self, _option, _opt, _value, _parser):
        '''Check whether we are in the service execution mode.'''
        if self.values.only_nodes and _option.dest is 'excluded_nodes':
            self.values.only_nodes.difference_update(_value)
        elif self.values.excluded_nodes and _option.dest is 'only_nodes':
            _value.difference_update(self.values.excluded_nodes)
        setattr(self.values, _option.dest, _value)
