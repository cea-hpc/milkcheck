#
# Copyright CEA (2011-2012)
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
This module contains the definition of the OptionParser for MilkCheck.
'''

from optparse import OptionParser, OptionGroup, Option
from copy import copy
from os.path import isdir
from ClusterShell.NodeSet import NodeSet, NodeSetException
from ClusterShell.NodeUtils import GroupResolverError
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
    except GroupResolverError, msg:
        raise InvalidOptionError('%s uses a wrong group' % msg)


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

        self.add_option('-d', '--debug', action='store_const',
                        dest='verbosity', const=5,
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

        eng.add_option('--define', '--var', '-D', action='append',
                       dest='defines', help='Define custom variables')

        eng.add_option('--nodeps', action='store_true', dest='nodeps',
                       default=False, help='Do not run dependencies')


        self.add_option_group(eng)

    def error(self, msg):
        '''Raise an exception when the parser gets an error.'''
        raise InvalidOptionError(' %s' % msg)

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
