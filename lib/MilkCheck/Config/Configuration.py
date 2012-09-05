# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

'''
This module contains the
'''

import sys
import yaml
import logging
import logging.config
from os import environ, listdir
from os.path import walk, isdir
from os.path import isfile
from re import match, compile, error

from MilkCheck.ServiceManager import service_manager_self
from MilkCheck.Engine.Service import Service
from MilkCheck.Engine.ServiceGroup import ServiceGroup, DepWrapper

class MilkCheckConfig(object):
    '''
    This class load the configuration files located within the specified
    directory
    '''
    def __init__(self, directory=None):
        self._filepath_base = '../conf/base/'
        self._flow = []

    def _go_through(self, arg, dirname=None, names=None):
        '''List the files in dirname'''
        for my_file in names:
            if isfile('%s/%s' %(dirname, my_file)) and \
                match('^[\w]*\.(yaml|yml)$', my_file):
                self.load_from_stream(
                    open('%s/%s' % (dirname, my_file),'r'))

    def load_from_dir(self, directory=None, recursive=False):
        '''
        Load configuration files located within a directory. This method
        will go though the overall file hierarchy.
        '''
        if directory and isdir(directory):
            if recursive:
                walk(directory, self._go_through, None)
            else:
                self._go_through(None, dirname=directory,
                    names=listdir(directory))
        else:
            raise ValueError("Invalid directory '%s'" % directory)
#            if recursive:
#                walk(self._filepath_base, self._go_through, None)
#            else:
#                self._go_through(None, dirname=self._filepath_base,
#                    names=listdir(self._filepath_base))

    def load_from_stream(self, stream):
        '''
        Load configuration from a stream. A stream could be a string or
        file descriptor
        '''
        # filter() removes empty statement.
        content = filter(None, yaml.safe_load_all(stream))
        if content:
            self._flow.extend(content)

    def build_graph(self):
        '''
        Build the graph from the content found in self._flow. It is required to
        call load methods before to call this one. If so self._flow will remain
        empty.
        '''
        if self._flow:
            self._build_services()

    def _build_services(self):
        '''
        Instanciate services, variables and service group. This methods
        also populate the service manager.
        '''
        # Get back the manager
        manager = service_manager_self()
        dependencies = {}

        # Go through data registred within flow
        for data in self._flow:
            for elem, subelems in data.items():
                # Parse variables
                if elem == 'variables':
                    for (varname, value) in subelems.items():
                        manager.add_var(varname, value)
                # Parse service
                elif elem == 'service' and 'actions' in subelems:
                    ser = Service(subelems['name'])
                    ser.fromdict(subelems)
                    wrap = self._parse_deps(subelems)
                    wrap.source = ser
                    dependencies[ser.name] = wrap
                # Parse service group
                elif elem == 'service' and 'services' in subelems:
                    ser = ServiceGroup(subelems['name'])
                    ser.fromdict(subelems)
                    wrap = self._parse_deps(subelems)
                    wrap.source = ser
                    dependencies[ser.name] = wrap
                else:
                    # XXX: Raise an exception with a better error handling
                    raise KeyError("Bad declaration of: %s" % elem)

        # Build relations between services
        for (sname, wrap) in dependencies.items():
            for (dtype, values) in wrap.deps.items():
                for dep in values:
                    wrap.source.add_dep(
                        target=dependencies[dep].source, sgth=dtype.upper())
        # Populate the manager and set up inheritance
        for wrap in dependencies.values():
            manager.register_service(wrap.source)

    def _parse_deps(self, data):
        '''Return a DepWrapper containing the different types of dependencies'''
        wrap = DepWrapper()
        for content in ('require', 'require_weak', 'check'):
            if content in data:
                if type(data[content]) is str:
                    wrap.deps[content] = [ data[content] ]
                else:
                    wrap.deps[content] = data[content]
        return wrap

    def get_data_flow(self):
        '''Get parsed data'''
        return self._flow

    data_flow = property(fget=get_data_flow)

class SyntaxChecker(object):
    '''
    This class is in charge of the control of the content parsed by the
    configuration object. It use a set of rules in order to check the values
    moreover it owns a logger able to specify to the user the different
    kinds of error.
    '''

    def __init__(self, file_rules_path=None):
        # Contains format rules by property
        self._rules = {}
        # Contains indications to evaluate misplaced properties
        self._places = {}
        # Contains the overall content
        checking = None
        logger = logging.getLogger('watcher')

        if not file_rules_path:
            file_rules_path = '%s/%s' \
            % (environ['PYTHONPATH'],'MilkCheck/Config/checksyn.yaml')
        try:
            checking = yaml.load(open('%s' %(file_rules_path),'r'))
        except IOError, exc:
            logger.error('Config file required syntax checking not found')
            sys.exit(2)
        except yaml.YAMLError, exc:
            if hasattr(exc, 'problem_mark'):
                logger.error('Error at line %d column %d'
                    %(exc.problem_mark.line+1, exc.problem_mark.column+1))
            else:
                logger.error('Error in configuration file : %s' % exc)
            sys.exit(2)
        except Exception, exc:
            logger.error('Unexpected error : %s' %exc)
        else:
            if 'places' in checking:
                self._places = checking['places']
            else:
                logger.error('Missing checking lement : places')
                sys.exit(2)
            if 'rules' in checking:
                self._rules = self._compile_regex_rules(checking['rules'])
            else:
                logger.error('Missing checking element : rules')
                sys.exit(2)

    def _compile_regex_rules(self, regexps):
        '''Compile all regex found in the dictionnary of rules : self._rules'''
        logger = logging.getLogger('watcher')
        rules = {}
        for rule in  regexps:
            regex = None
            try:
                regex = compile(regexps[rule])
            except error, exc:
                logger.warning('%s : %s' % (exc, regexps[rule]))
            else:
                rules[rule] = regex
        return rules

    def validate(self, filepath_doc):
        '''Call the different checker defined in this class'''
        doc_valid = True
        # Load YAML target file
        config = MilkCheckConfig()
        config.load_from_stream(open(filepath_doc,'r'))
        # Validation sequence
        if config.data_flow:
            if not self._validate_placement(config.data_flow):
                return False
        else:
            return False
        return doc_valid

    def _validate_placement(self, data):
        '''Validate the place of the different properties in the document.'''
        pass

    def _validate_content(self, data):
        '''
        Validate the content of the different properties in using self.rules.
        '''
        pass
