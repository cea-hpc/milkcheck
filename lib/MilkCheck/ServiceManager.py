# Copyright CEA (2011)
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

'''
This module contains the ServiceManager class definition.
'''

# Classes
from MilkCheck.EntityManager import EntityManager
from MilkCheck.Engine.Service import Service
from MilkCheck.Engine.Action import Action

# Exceptions
from MilkCheck.Engine.BaseEntity import MilkCheckEngineError
from MilkCheck.Engine.BaseEntity import VariableAlreadyReferencedError

# Symbols
from MilkCheck.Engine.BaseEntity import LOCKED

class ServiceNotFoundError(MilkCheckEngineError):
    '''
    Define an exception raised when you are looking for a service
    that does not exist.
    '''
    def __init__(self, message='Service is not referenced by the manager'):
        MilkCheckEngineError.__init__(self, message)

class ServiceAlreadyReferencedError(MilkCheckEngineError):
    '''
    Define an exception raised when you tried to register a services which
    is already referenced by the manager.
    '''
    def __init__(self, message='Service is already referenced by the manager'):
        MilkCheckEngineError.__init__(self, message)

class ServiceManager(EntityManager):
    '''
    The service manager has to handle call to services. It implements
    features allowing us to get dependencies of service and so on.
    '''
    
    def __init__(self):
        EntityManager.__init__(self)
        # Variables declared in the global scope
        self.variables = {}
        # Status of the graph
        self._graph_changed = False

    def __refresh_graph(self):
        '''Reinitialize the right values for the graph of services'''
        for service in self.entities.values():
            service.reset()
        self._graph_changed = False
            
    def has_service(self, service):
        '''Determine if the service is registered within the manager'''
        return service in self.entities.values()

    def add_var(self, varname, value):
        '''Add a symbol within the service manager'''
        if varname not in self.variables:
            self.variables[varname] = value
        else:
            raise VariableAlreadyReferencedError

    def remove_var(self, varname):
        '''Remove var from the the service manager'''
        if varname in self.variables:
            del self.variables[varname]

    def reset(self):
        '''Clean object service manager.'''
        self.variables.clear()
        self.entities.clear()

    def register_service(self, service):
        '''Add a new service to the manager.'''
        assert service, 'service added cannot be None'
        if service.name in self.entities:
            raise ServiceAlreadyReferencedError
        else:
            self.entities[service.name] = service

    def register_services(self, *args):
        '''Add all services referenced by args'''
        for service in args:
            self.register_service(service)
        
    def forget_service(self, service):
        '''
        Remove the service from the manager. It takes care of the relations
        with others services in order to avoid to get a graph with a bad format.
        '''
        assert service, 'The service that you want to forget cannot be None'
        if not self.has_service(service):
            raise ServiceNotFoundError
        else:
            dependencies = []
            switch = len(service.children)
            dependencies.extend(service.children.values())
            dependencies.extend(service.parents.values())
            for dep in dependencies:
                switch -= 1
                if switch > 0:
                    service.remove_dep(dep.target.name, parent=False)
                else:
                    service.remove_dep(dep.target.name)
            del self.entities[service.name]

    def forget_services(self, *args):
        '''Remove all specified services from the manager'''
        for service in args:
            self.forget_service(service)

    def _apply_options(self, options):
        '''
        This apply a sequence of modifications on the graph. A modification
        can be an update of the nodes usable by the services or whatever that
        is referenced within options.  
        '''
        # Load the configuration located within the directory
        if options.config_dir:
            self.reset()
            if options.hijack_nodes:
                self.add_var('EXCLUDED_NODES', options.hijack_nodes)
            else:
                self.add_var('EXCLUDED_NODES', '')
            self.load_config(options.config_dir)

        # Avoid some of the services referenced in the graph
        if options.excluded_svc:
            self.__lock_services(options.excluded_svc)

        # Use just those nodes 
        if options.only_nodes:
            self.__update_usable_nodes(options.only_nodes, 'INT')
        # Avoid those nodes
        elif options.hijack_nodes:
            self.__update_usable_nodes(options.hijack_nodes, 'DIF')

    def __lock_services(self, services):
        '''
        Lock all services specified in the list. This will assign the LOCKED
        status on the services. A soon as a service is locked it will never be
        processed.
        '''
        for service in services:
            if service in self.entities:
                self.entities[service].status = LOCKED

    def __update_usable_nodes(self, nodeset, mode=None):
        '''
        Update target value used by the service and the elements linked to
        the service.
        '''
        assert mode in (None, 'DIF', 'INT'), \
            'Invalid mode, should be DIF, INT or None'
        for service in self.entities.values():
            service.update_target(nodeset, mode)
    
    def call_services(self, services, action, opts=None):
        '''Allow the user to call one or multiple services.'''
        assert action, 'action name cannot be None'

        # Make sure that the graph is usable
        if self._graph_changed:
            self.__refresh_graph()
        # Apply options over the graph
        if opts:
            self._apply_options(opts)
        # Service are going to use reversed algorithms
        reverse = False
        if action == 'stop':
            reverse = True
            self._reverse_mod(reverse)

        # Perform all services
        if not services:
            source = Service('src')
            source.simulate = True
            source.add_action(Action(name=action,command=':'))
            if reverse:
                source.algo_reversed = True
            for service in self.entities.values():
                if reverse and not service.parents:
                    service.add_dep(target=source)
                elif not reverse and not service.children:
                    source.add_dep(target=service)
            source.run(action)
            if reverse:
                source.clear_child_deps()
            else:
                source.clear_parent_deps()
            self._graph_changed = True
        # Perform the required service
        elif len(services) == 1:
            if services[0] in self.entities:
                self.entities[services[0]].run(action)
                self._graph_changed = True
            else:
                raise ServiceNotFoundError('Undefined service [%s]'
                    % services[0])
        # Perform required services
        else:
            source = Service('src')
            source.simulate = True
            if reverse:
                source.algo_reversed = True
            source.add_action(Action(name=action,command=':'))
            for service in services:
                if service in self.entities:
                    if reverse:
                        self.entities[service].add_dep(target=source)
                    else:
                        source.add_dep(target=self.entities[service])
                else:
                    raise ServiceNotFoundError('Undefined service [%s]'
                        %service)
            source.run(action)
            if reverse:
                source.clear_child_deps()
            else:
                source.clear_parent_deps()
            self._graph_changed = True

    def load_config(self, conf):
        '''
        Load the configuration within the manager thanks to MilkCheckConfig
        '''
        from MilkCheck.Config.Configuration import MilkCheckConfig
        config = MilkCheckConfig()
        config.load_from_dir(directory=conf)
        config.build_graph()

def service_manager_self():
    '''Return a singleton instance of a service manager'''
    if not ServiceManager._instance:
        ServiceManager._instance = ServiceManager()
    return ServiceManager._instance
