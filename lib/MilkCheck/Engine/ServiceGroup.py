#
# Copyright CEA (2011-2017)
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

"""
This module contains the ServiceGroup class definition
"""

# Classes
from ClusterShell.NodeSet import NodeSet
from MilkCheck.Engine.Service import Service
from MilkCheck.Engine.BaseEntity import BaseEntity, DEP_ORDER

# Symbols
from MilkCheck.Engine.BaseEntity import DONE, SKIPPED, REQUIRE, MISSING, \
                                        DEP_ERROR, NO_STATUS

from MilkCheck.Engine.BaseEntity import UnknownDependencyError
from MilkCheck.Engine.BaseEntity import MilkCheckEngineError


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

class ServiceGroup(Service):
    """
    This class models a group of service. A group of service
    can own actions it's no mandatory. However it shall have
    subservices
    """

    def __init__(self, name, target=None):
        Service.__init__(self, name, target)
        # Entry point of the group
        self._source = Service('source')
        self._source.simulate = True
        self._source.add_dep(target=self, parent=False)
        del self.parents['source']
        self._sink = Service('sink')
        self._sink.simulate = True
        # subservices
        self._subservices = {}

    def update_target(self, nodeset, mode=None):
        '''Update the attribute target of a ServiceGroup'''
        BaseEntity.update_target(self, nodeset, mode)
        for service in self._subservices.values():
            service.update_target(nodeset, mode)

    def filter_nodes(self, nodes):
        """
        Add error nodes to skip list.

        Nodes in this list will not be used when launching actions.
        """
        BaseEntity.filter_nodes(self, nodes)
        for service in self._subservices.values():
            service.filter_nodes(nodes)

    def iter_subservices(self):
        '''Return an iterator over the subservices'''
        for svc in self._subservices.values():
            yield svc

    def reset(self):
        '''Reset values of attributes in order to perform multiple exec'''
        Service.reset(self)
        for service in self._subservices.values():
            service.reset()
        self._sink.reset()
        self._source.reset()
        
    def search(self, name, reverse=False):
        """Look for a node through the overall graph"""
        target = None
        if reverse:
            target = self._sink.search(name, reverse)
        else:
            target = self._source.search(name)
        if target:
            return target
        else:
            return Service.search(self, name, reverse)
    
    def has_subservice(self, name):
        """
        Check if the service is referenced within the group
        """
        return name in self._subservices

    def has_action(self, action_name):
        """
        A group consider to get an action only if both source and sink
        own the action
        """
        for svc in self.iter_subservices():
            if svc.has_action(action_name):
                return True
        return False

    def skip(self):
        """Skip all services from this group"""
        for svc in self.iter_subservices():
            svc.skip()

    def to_skip(self, action):
        """
        Tell if group should be skipped for provided action name.

        That means that all its subservices should be skipped.
        """
        for svc in self._subservices.values():
            if not svc.to_skip(action):
                return False
        return True

    def add_inter_dep(self, target, base=None, sgth=REQUIRE):
        """
        Add dependency in the subgraph. Adding a dependency in using this
        method means that the target will be an internal dependency of the
        group
        """
        if base and not self.has_subservice(base.name):
            raise ServiceNotFoundError()
        # A base node is specified so hook target on it
        if base:
            if not target.has_parent_dep('sink'):
                target.add_dep(target=self._sink)
            if not target.children:
                target.add_dep(target=self._source, parent=False)
            base.add_dep(target=target, sgth=sgth)
        # Target is hooked on source and sink
        else:
            self._sink.add_dep(target=target, sgth=sgth, parent=False)
            self._source.add_dep(target=target, sgth=sgth)
        self._subservices[target.name] = target
        target.parent = self
        self.__update_edges()

    def __update_edges(self, create_links=False):
        '''Update edges of the subgraph'''
        for abs_ser in (self._source, self._sink):
            if create_links:
                for service in self._subservices.values():
                    if not service.parents:
                        self._sink.add_dep(target=service, parent=False)
                    if not service.children:
                        self._source.add_dep(target=service)
            else:
                if abs_ser is self._source:
                    deps = abs_ser.parents
                else:
                    deps = abs_ser.children
                for dep in deps.copy().values():
                    # If direct dependency of source have more than one child
                    # remove this dependency
                    if abs_ser is self._source and len(dep.target.children) > 1:
                        dep.target.remove_dep('source', parent=False)
                    # If direct dependency of source have more than one parent
                    # remove this dependency
                    elif abs_ser is self._sink and len(dep.target.parents) > 1:
                        dep.target.remove_dep('sink')
                
                
    def remove_inter_dep(self, dep_name):
        """
        Remove a dependency on both side, in the current object and in the
        target object concerned by the dependency
        """
        if not self.has_subservice(dep_name):
            raise ServiceNotFoundError()
        else:
            for dep in self._subservices[dep_name].parents.copy().values():
                dep.target.remove_dep(dep_name, parent=False)
            for dep in self._subservices[dep_name].children.copy().values():
                dep.target.remove_dep(dep_name)
            del self._subservices[dep_name]
            self.__update_edges(True)
            
    def graph_info(self):
        """ Return a tuple to manage dependencies output """
        return ("%s.__hook" % self.fullname(), "cluster_%s" % self.fullname())

    def graph(self, excluded=None):
        """ Generate a subgraph of dependencies in the ServiceGroup"""
        grph = ''
        grph += 'subgraph "cluster_%s" {\nlabel="%s";\n' % (self.fullname(),
                                                              self.fullname())
        grph += 'style=rounded;\nnode [style=filled];\n'

        # Create a default node to manage DOT output
        # __hook will be used to attach the nodes to the subgraph
        grph += '"%s.__hook" [style=invis];\n' % self.fullname()

        # Graph content of the servicegroup
        entities = self._subservices
        for ent in entities.values():
            if not ent.excluded(excluded):
                grph += ent.graph(excluded=excluded)
        grph += '}\n'

        # Graph dependencies of the service group
        for dep in self.deps().values():
            if not dep.target.excluded(excluded):
                if not dep.target.simulate:
                    grph += dep.graph(self)
        return grph

    def eval_deps_status(self):
        """
        Evaluate the result of the dependencies in order to check
        if we have to continue in normal mode or in a degraded mode.
        """
        extd_status = Service.eval_deps_status(self)
        intd_status = DONE
        if self._algo_reversed:
            intd_status = self._sink.eval_deps_status()
        else:
            intd_status = self._source.eval_deps_status()

        if DEP_ORDER[extd_status] > DEP_ORDER[intd_status]:
            return extd_status
        else:
            return intd_status

    def _launch_action(self, action, status):
        """
        ServiceGroup does not have real action, but internal services instead.

        Launch internal services if needed or just set group status.
        Group status is based on its internal status. 
        """

        # Check if the action is MISSING in the whole group.
        if not self.has_action(action):
            self.update_status(MISSING)
        # Check if the whole group is SKIPPED
        elif self.to_skip(action):
            self.update_status(SKIPPED)
        # If there is a dep error, we should not run anything
        elif status == DEP_ERROR:
            self.update_status(DEP_ERROR)
        # No dep error, try to run internal services
        elif self._algo_reversed and self._sink.children and \
               self._sink.status is NO_STATUS:
            self._sink.prepare(action)
        elif not self._algo_reversed and self._source.parents and \
               self._source.status is NO_STATUS:
            self._source.prepare(action)
        # No service to run, just update status
        else:
            if self._algo_reversed:
                intd_status = self._sink.eval_deps_status()
            else:
                intd_status = self._source.eval_deps_status()
            self.update_status(intd_status)

    def inherits_from(self, entity):
        '''Inherit properties from entity'''
        BaseEntity.inherits_from(self, entity)
        for subservice in self.iter_subservices():
            subservice.inherits_from(self)

    def set_algo_reversed(self, flag):
        """Updates dependencies if reversed flag is specified"""
        if self._algo_reversed and not flag:
            del self._sink.parents[self.name]
            self._source.add_dep(target=self, parent=False)
            del self.parents['source']
        elif not self._algo_reversed and flag:
            del self._source.children[self.name]
            self._sink.add_dep(target=self)
            del self.children['sink']
        for service in self._subservices.values():
            service.algo_reversed = flag
        self._algo_reversed = flag
        self._sink._algo_reversed = flag
        self._source._algo_reversed = flag

    algo_reversed = property(fset=set_algo_reversed)

    def fromdict(self, grpdict):
        """Populate group attributes from dict."""
        BaseEntity.fromdict(self, grpdict)

        if 'services' in grpdict:
            dep_mapping = {}

            # Wrap dependencies from YAML and build the service
            for names, props in grpdict['services'].items():
                for subservice in NodeSet(names):

                    # Parsing dependencies
                    wrap = DepWrapper()
                    for prop in ('require', 'require_weak', 'require_filter',
                                 'filter', 'before', 'after', 'check'):
                        if prop in props:
                            if prop in ('before', 'after'):
                                props['require_weak'] = props[prop]
                                prop = 'require_weak'
                            # Only for compat with v1.1beta versions
                            if prop == 'require_filter':
                                props['filter'] = props[prop]
                                prop = 'filter'
                            wrap.deps[prop] = props[prop]

                    # Get subservices which might be Service or ServiceGroup
                    service = None
                    if 'services' in props:
                        service = ServiceGroup(subservice)
                    else:
                        service = Service(subservice)

                    # Link the group and its new subservice together
                    self._subservices[subservice] = service
                    service.parent = self

                    # Populate based on dict content
                    service.fromdict(props)

                    wrap.source = service
                    dep_mapping[subservice] = wrap

            # Generate dependency links of the service
            for wrap in dep_mapping.values():
                # Not any dependencies so just attach
                for dtype in wrap.deps:
                    wrap.deps[dtype] = wrap.source._resolve(wrap.deps[dtype])

                    # For simplicity, supports deps as a single service
                    if type(wrap.deps[dtype]) is str:
                        wrap.deps[dtype] = [wrap.deps[dtype]]

                    for dep in wrap.deps[dtype]:
                        if dep not in self._subservices:
                            raise UnknownDependencyError(dep)
                        wrap.source.add_dep(self._subservices[dep],
                                                         sgth=dtype.upper())

            # Bind subgraph to the service group
            for service in self.iter_subservices():
                if not service.children:
                    service.add_dep(self._source, parent=False)
                if not service.parents:
                    service.add_dep(self._sink)

        for subser in self.iter_subservices():
            subser.inherits_from(self)

    def resolve_all(self):
        """Resolve all variables in ServiceGroup properties"""
        BaseEntity.resolve_all(self)
        for subser in self.iter_subservices():
            subser.resolve_all()


class DepWrapper(object):
    '''
    Tool class allowing us to wrap the dependencies of a service. This
    class is used by the factory in order to provide an easiest way to
    to deal with dependencies.
    '''

    def __init__(self):
        self.source = None
        self.deps = {'require': [], 'require_weak': [], 'check': [],
                     'filter': []}
