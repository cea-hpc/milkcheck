# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

'''
This module contains the
'''
import yaml
import logging
import logging.config
from sys import exit
from os import environ, listdir
from os.path import walk, isdir
from os.path import isfile, abspath
from re import match, compile, error
from MilkCheck.ServiceManager import service_manager_self
from MilkCheck.Engine.ServiceFactory import ServiceFactory, DepWrapper
from MilkCheck.Engine.ServiceFactory import ServiceGroupFactory

class MilkCheckConfig(object):
    '''
    This class load the configuration files located within the specified
    directory
    '''
    def __init__(self, directory=None):
        self._filepath_base = '../conf/base/'
        self._flow = []
        logging.config.fileConfig(environ['PYTHONPATH']+
            '/MilkCheck/Log/mc_logging.conf')

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
            if recursive:
                walk(self._filepath_base, self._go_through, None)
            else:
                self._go_through(None, dirname=self._filepath_base,
                    names=listdir(self._filepath_base))

    def load_from_stream(self, stream):
        '''
        Load configuration from a stream. A stream could be a string or
        file descriptor
        '''
        content = None
        logger = logging.getLogger('watcher')
        content = yaml.safe_load_all(stream)
        if content:
            self._flow.extend(content)

    def build_graph(self):
        '''
        Build the graph from the content found in self._flow. It is required to
        call load methods before to call this one. If so self._flow will remain
        empty.
        '''
        if self._flow:
            manager = service_manager_self()
            self._build_services()

    def _build_services(self):
        '''
        Instanciate services, variables and service group. This methods
        also populate the service manager.
        '''
        # Get back the manager
        manager = service_manager_self()

        dependencies = {}
        variables = {}

        # Go through data registred within flow
        for data in self._flow:
            # Parse variables
            if 'variables' in data:
                for (varname, value) in data['variables'].items():
                    manager.add_var(varname, value)
            # Parse service
            elif 'service' in data and 'actions' in data['service']:
                ser = ServiceFactory.create_service_from_dict(data)
                wrap = self._parse_deps(data['service'])
                wrap.source = ser
                dependencies[ser.name] = wrap
            # Parse service group
            elif 'service' in data and 'services' in data['service']:
                ser = ServiceGroupFactory.create_servicegroup_from_dict(data)
                wrap = self._parse_deps(data['service'])
                wrap.source = ser
                dependencies[ser.name] = wrap
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
        if 'require' in data:
            wrap.deps['require'] = data['require']
        if 'require_weak' in data:
            wrap.deps['require_weak'] = data['require_weak']
        if 'check' in data:
            wrap.deps['check'] = data['check']
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

        # HAS TO BE REMOVED AND SET UP IN THE MAIN
        logging.config.fileConfig(environ['PYTHONPATH']+
            '/MilkCheck/Log/mc_logging.conf')
        logger = logging.getLogger('watcher')

        if not file_rules_path:
            file_rules_path = '%s/%s'\
            %(environ['PYTHONPATH'],'MilkCheck/Config/checksyn.yaml')
        try:
            checking = yaml.load(open('%s' %(file_rules_path),'r'))
        except IOError, exc:
            logger.error('Config file required syntax checking not found')
            exit(2)
        except yaml.YAMLError, exc:
            if hasattr(exc, 'problem_mark'):
                logger.error('Error at line %d column %d'
                    %(exc.problem_mark.line+1, exc.problem_mark.column+1))
            else:
                logger.error('Error in configuration file : %s' % exc)
            exit(2)
        except Exception, exc:
            logger.error('Unexpected error : %s' %exc)
        else:
            if 'places' in checking:
                self._places = checking['places']
            else:
                logger.error('Missing checking lement : places')
                exit(2)
            if 'rules' in checking:
                self._rules = self._compile_regex_rules(checking['rules'])
            else:
                logger.error('Missing checking element : rules')
                exit(2)

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