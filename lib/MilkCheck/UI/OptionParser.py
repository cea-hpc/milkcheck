# Copyright CEA (2011)
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

'''
This module contains the definition of the OptionParser for MilkCheck.
'''

from optparse import OptionParser, OptionGroup, Option
from copy import copy
from os.path import isdir
from ClusterShell.NodeSet import NodeSet, NodeSetException

# MilkCheck version
__VERSION__ = 1.0
__LAST_RELEASE__ = 'Friday, July 2011'

class InvalidOptionError(Exception):
    '''Exception raised when the parser ran against an unexpected option.'''
    pass

def check_nodeset(option, opt, value):
    '''Try to build a nodeset from the option value.'''
    try:
        return NodeSet(value)
    except NodeSetException:
        raise InvalidOptionError('%s is not a valid nodeset' % value)


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
        OptionParser.__init__(self, usage,
            version=__VERSION__, option_class=option_class, **kwargs)

    def configure_mop(self):
        '''Populate the parser with the specified options.'''
        # Display options
        self.add_option('-v', '--verbose', action='count', dest='verbosity',
                        default=1, help='Increase or decrease verbosity')

        self.set_conflict_handler('resolve')
        self.add_option('-v', '--version', action='callback',
                        callback=self.__check_version_mode, dest='version',
                        help='Version number of MilkCheck')

        self.add_option('-d', '--debug', action='callback',
                        callback=self.__config_debug, dest='debug',
                        help='Set debug mode and maximum verbosity')

        # Configuration options
        self.add_option('-c', '--config-dir', action='callback',
                        callback=self.__check_dir, type='string',
                        dest='config_dir',
                        help='Change configuration files directory')

        # Display dependencies option
        self.add_option('-p', '--printdeps', action='callback',
                        callback=self.__check_printdep_mode,
                        dest='print_servs',
                        help='Print dependencies of the specified service')

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

        self.add_option_group(eng)

    def error(self, msg):
        '''Raise an exception when the parser gets an error.'''
        raise InvalidOptionError(' %s' % msg)

    def __config_debug(self, option, opt, value, parser):
        '''Configure the debug mode when the parser gets the option -d.'''
        self.values.verbosity = 5
        self.values.debug = True

    def __check_dir(self, option, opt, value, parser):
        '''Check the content of the option -c'''
        if value and isdir(value):
            setattr(self.values, option.dest, value)
        else:
            self.error('-c/--config-dir should be a valid directory')


    def __check_version_mode(self, option, opt, value, parser):
        '''Check that not any option is used with --version'''
        setattr(self.values, option.dest, 'MilkCheck %s - Last release on %s'
        % (self.version, __LAST_RELEASE__))

    def __check_printdep_mode(self, option, opt, value, parser):
        '''Check whether we are in printdeps mode.'''
        if self.values.only_nodes or \
                self.values.excluded_nodes or \
                    self.values.hijack_servs:
            self.error('%s cannot be used with -n, -x or -X' % option)
        self.__consume_args_callback(option, value)
        if not self.values.print_servs:
            self.error('%s service names are missing' % option)

    def __check_service_mode(self, option, opt, value, parser):
        '''Check whether we are in the service execution mode.'''
        if self.values.print_servs:
            self.error('%s cannot be used with -n, -x or -X' % option)
        elif option.dest in ('only_nodes', 'excluded_nodes'):
            if self.values.only_nodes and option.dest is 'excluded_nodes':
                self.values.only_nodes.difference_update(value)
            elif self.values.excluded_nodes and option.dest is 'only_nodes':
                value.difference_update(self.values.excluded_nodes)
            setattr(self.values, option.dest, value)
