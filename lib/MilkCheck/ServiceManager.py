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
This module contains the ServiceManager class definition.
'''

# Classes
from MilkCheck.EntityManager import EntityManager
from MilkCheck.Engine.Service import Service
from MilkCheck.Engine.Action import Action

# Exceptions
from MilkCheck.Engine.BaseEntity import MilkCheckEngineError
from MilkCheck.Engine.BaseEntity import VariableAlreadyExistError

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
    def __init__(self, svcname):
        message = "Service '%s' is already referenced by the manager" % svcname
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
        # Top service
        self.source = Service('root')
        self.source.simulate = True

    def __refresh_graph(self, reverse):
        '''Reinitialize the right values for the graph of services'''
        for service in self.entities.values():
            service.reset()
        if reverse:
            self.source.clear_child_deps()
        else:
            self.source.clear_parent_deps()

    def has_service(self, service):
        '''Determine if the service is registered within the manager'''
        return service in self.entities.values()

    def add_var(self, varname, value):
        '''Add a symbol within the service manager'''
        if varname not in self.variables:
            self.variables[varname] = value
        else:
            raise VariableAlreadyExistError

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
            raise ServiceAlreadyReferencedError(service.name)
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

    def _variable_config(self, conf):
        '''Automatic variables based on MilckCheck configuration.'''
        if conf:
            # -n NODES
            self.add_var('SELECTED_NODES', str(conf.get('only_nodes', '')))
            # -x NODES
            self.add_var('EXCLUDED_NODES', str(conf.get('excluded_nodes', '')))
        else:
            for varname in ('selected_node', 'excluded_nodes'):
                self.add_var(varname.upper(), '')

    def _apply_config(self, conf):
        '''
        This apply a sequence of modifications on the graph. A modification
        can be an update of the nodes usable by the services or whatever that
        is referenced within configuration.
        '''

        # Load the configuration located within the directory
        if conf.get('config_dir'):
            self.entities.clear()
            self.load_config(conf['config_dir'])

        # Avoid some of the services referenced in the graph
        if conf.get('excluded_svc'):
            self.__lock_services(conf['excluded_svc'])

        # Use just those nodes 
        if conf.get('only_nodes'):
            self.__update_usable_nodes(conf['only_nodes'], 'INT')
        # Avoid those nodes
        elif conf.get('excluded_nodes'):
            self.__update_usable_nodes(conf['excluded_nodes'], 'DIF')

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

    def call_services(self, services, action, conf=None):
        '''Allow the user to call one or multiple services.'''
        assert action, 'action name cannot be None'

        # Manage reverse mode based on configuration
        reverse = False
        if conf:
            reverse = action in conf.get('reverse_actions')

        self.variables.clear()

        # Create global variable from configuration
        self._variable_config(conf)

        # Make sure that the graph is usable
        self.__refresh_graph(reverse)
        # Apply configuration over the graph
        if conf:
            self._apply_config(conf)

        self.source.reset()
        # Enable reverse mode if needed
        self._reverse_mod(reverse)
        self.source.algo_reversed = reverse

        if not self.source.has_action(action):
            self.source.add_action(Action(name=action, command=':'))
        # Perform all services
        if not services:
            for service in self.entities.values():
                if reverse and not service.parents:
                    service.add_dep(target=self.source)
                elif not reverse and not service.children:
                    self.source.add_dep(target=service)
        # Perform required services
        else:
            for service_name in services:
                if service_name in self.entities:
                    if reverse:
                        self.entities[service_name].add_dep(target=self.source)
                    else:
                        self.source.add_dep(target=self.entities[service_name])
                else:
                    raise ServiceNotFoundError('Undefined service [%s]'
                        % service_name)
        self.source.run(action)

    def output_graph(self, services=None, excluded=None):
        """Return entities graph (DOT format)"""
        grph = "digraph dependency {\n"
        grph += "compound=true;\n"
        #grph += "node [shape=circle];\n"
        grph += "node [style=filled];\n"
        for service in (services or self.entities):
            if not self.entities[service].excluded(excluded):
                grph += self.entities[service].graph(excluded)
        grph += '}\n'
        return grph

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
