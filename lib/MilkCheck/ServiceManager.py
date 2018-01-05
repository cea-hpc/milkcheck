#
# Copyright CEA (2011-2014)
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

from MilkCheck.Engine.BaseEntity import DependencyAlreadyReferenced
from MilkCheck.Engine.BaseEntity import LOCKED, WARNING

from MilkCheck.Engine.ServiceGroup import ServiceGroup
from MilkCheck.Engine.ServiceGroup import ServiceNotFoundError, \
                                          ServiceAlreadyReferencedError


class ServiceManager(ServiceGroup):
    '''
    The service manager has to handle call to services. It implements
    features allowing us to get dependencies of service and so on.
    '''

    def __init__(self, name="MAIN"):
        ServiceGroup.__init__(self, name)
        self.simulate = True

        # XXX: Only for compat with tests
        self.entities = self._subservices

    def fullname(self):
        return ""

    def has_warnings(self):
        '''Determine if the service has one action with the WARNING status'''
        for ent in self.iter_subservices():
            if ent.status is WARNING:
                return True
        return False

    #
    # Service management helpers
    #

    def has_service(self, service):
        '''Determine if the service is registered within the manager'''
        return self.has_subservice(service.name)

    def register_service(self, service):
        '''Add a new service to the manager.'''
        try:
            self.add_inter_dep(service)
        except DependencyAlreadyReferenced:
            raise ServiceAlreadyReferencedError(service.name)

    def register_services(self, *args):
        '''Add all services referenced by args'''
        for service in args:
            self.register_service(service)

    def forget_service(self, service):
        '''
        Remove the service from the manager. It takes care of the relations
        with others services in order to avoid to get a graph with a bad format.
        '''
        self.remove_inter_dep(service.name)

    def forget_services(self, *args):
        '''Remove all specified services from the manager'''
        for service in args:
            self.forget_service(service)

    #
    #
    #

    def _variable_config(self, conf):
        '''Automatic variables based on MilckCheck configuration.'''
        if conf:
            # -n NODES
            self.add_var('SELECTED_NODES', str(conf.get('only_nodes', '')))
            # -x NODES
            self.add_var('EXCLUDED_NODES', str(conf.get('excluded_nodes', '')))

            # Add command line variable
            for defines in conf.get('defines', []):
                for define in defines.split():
                    key, value = define.split('=', 1)
                    self.add_var(key, value)
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
            self.load_config(conf['config_dir'])

        # Avoid some of the services referenced in the graph
        if conf.get('excluded_svc'):
            for service in self.iter_subservices():
                if service.name in conf['excluded_svc']:
                    service.status = LOCKED

        if conf.get('tags'):
            for svc in self.iter_subservices():
                if not svc.match_tags(conf['tags']):
                    svc.skip()

        # Use just those nodes
        if conf.get('only_nodes') is not None:
            self.update_target(conf['only_nodes'], 'INT')
        # Avoid those nodes
        elif conf.get('excluded_nodes') is not None:
            self.update_target(conf['excluded_nodes'], 'DIF')

    def select_services(self, services):
        """Disable all services except those from 'services'"""
        for svcname in services:
            if not self.has_subservice(svcname):
                raise ServiceNotFoundError('Undefined service [%s]' % svcname)

        parent = not self._algo_reversed
        if parent:
            spot = self._source
        else:
            spot = self._sink

        # Remove unused services
        for service in spot.deps().keys():
            if service not in services:
                spot.remove_dep(service, parent=parent)
        # Add direct link to important services
        for service in services:
            if service not in spot.deps():
                svc = self._subservices[service]
                spot.add_dep(svc, parent=parent)

    def _disable_deps(self):
        """Clear internal dependencies from enabled services"""
        if self._algo_reversed:
            for dep in self._sink.children.values():
                dep.target.clear_child_deps()
        else:
            for dep in self._source.parents.values():
                dep.target.clear_parent_deps()

    def call_services(self, services, action, conf=None):
        '''Allow the user to call one or multiple services.'''

        # Make sure that the graph is usable
        self.reset()
        self.variables.clear()

        # Create global variable from configuration
        self._variable_config(conf)
        if conf:
            # Apply configuration over the graph
            self._apply_config(conf)
            # Enable reverse mode if needed, based on config
            self.algo_reversed = action in conf.get('reverse_actions')

        # Ensure all variables have been resolved
        self.resolve_all()

        # Adapt the graph for required services
        if services:
            self.select_services(services)

        if conf and conf.get('nodeps'):
            self._disable_deps()

        self.run(action)

    def output_graph(self, services=None, excluded=None):
        """Return service graph (DOT format)"""
        grph = "digraph dependency {\n"
        grph += "compound=true;\n"
        #grph += "node [shape=circle];\n"
        grph += "node [style=filled];\n"
        for service in (services or self._subservices):
            if not self._subservices[service].excluded(excluded):
                grph += self._subservices[service].graph(excluded)
        grph += '}\n'
        return grph

    def load_config(self, conf):
        '''
        Load the configuration within the manager thanks to MilkCheckConfig
        '''
        from MilkCheck.config import load_from_dir
        self.fromdict(load_from_dir(conf))
