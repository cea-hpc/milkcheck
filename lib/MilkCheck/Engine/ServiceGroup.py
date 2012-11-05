# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This module contains the ServiceGroup class definition
"""

# Classes
from ClusterShell.NodeSet import NodeSet
from MilkCheck.Engine.Service import Service, Action
from MilkCheck.Engine.BaseEntity import BaseEntity, DEP_ORDER, Dependency

# Symbols
from MilkCheck.Engine.BaseEntity import DONE, WARNING, SKIPPED, REQUIRE, \
                                        MISSING

# Exceptions
from MilkCheck.ServiceManager import ServiceNotFoundError

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
        '''Update the attribute target of a service'''
        assert nodeset, 'The nodeset cannot be None'
        if not mode:
            self.target = nodeset
        elif mode is 'DIF' and self.target:
            self.target.difference_update(nodeset)
        elif mode is 'INT' and self.target:
            self.target.intersection_update(nodeset)
        for service in self._subservices.values():
            service.update_target(nodeset, mode)

    def iter_subservices(self):
        '''Return an iterator over the subservices'''
        return self._subservices.itervalues()

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
        return self._source.has_action(action_name) and \
                    self._sink.has_action(action_name)
    
    def add_inter_dep(self, target, base=None, sgth=REQUIRE):
        """
        Add dependency in the subgraph. Adding a dependency in using this
        method means that the target will be an internal dependency of the
        group
        """
        if base and not self.has_subservice(base.name):
            raise ServiceNotFoundError()
        # Generate fake actions
        for name in target._actions:
            if name not in self._source._actions:
                self._source.add_action(Action(name, delay=0.01))
            if name not in self._sink._actions:
                self._sink.add_action(Action(name, delay=0.01))
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
                for dep in deps.values():
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
            for dep in self._subservices[dep_name].parents.values():
                dep.target.remove_dep(dep_name, parent=False)
            for dep in self._subservices[dep_name].children.values():
                dep.target.remove_dep(dep_name)
            del self._subservices[dep_name]
            self.__update_edges(True)
            
    def search_deps(self, symbols=None):
        '''
        Return a dictionnary of dependencies both external and internal.
        In order to be in the dictionnary the dependencies must have a status
        matching to a symbol in symbols.
        '''
        depmap = {}
        depmap['internal'] = []
        depmap['external'] = Service.search_deps(self, symbols)
        if self._algo_reversed and self._sink.children and \
            self._sink.status in symbols:
            depmap['internal'].append(Dependency(self._sink))
        elif not self._algo_reversed and self._source.parents and \
            self._source.status in symbols:
            depmap['internal'].append(Dependency(self._source))
        return depmap

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

    def _process_dependencies(self, deps):
        '''perform a prepare on each dependencies in deps'''
        assert deps, 'deps cannot be none'
        if deps['external'] or deps['internal']:
            # Before to start internal dependencies we have to be sure
            # that all external dependencies are solve
            if deps['external']:
                for external in deps['external']:
                    if external.is_check():
                        external.target.prepare('status')
                    else:
                        external.target.prepare(self._last_action)
            elif deps['internal']:
                for internal in deps['internal']:
                    if internal.is_check():
                        internal.target.prepare('status')
                    else:
                        internal.target.prepare(self._last_action)
        else:
            if self._algo_reversed:
                intd_status = self._sink.status
            else:
                intd_status = self._source.status

            # The group node is a fake we just change his status
            if intd_status in (SKIPPED, MISSING):
                self.update_status(intd_status)
            elif self.warnings:
                self.update_status(WARNING)
            else:
                self.update_status(DONE)

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
                    for prop in ('require', 'require_weak', 'check'):
                        if prop in props:
                            wrap.deps[prop] = props[prop]

                    # Get subservices which might be Service or ServiceGroup
                    service = None
                    if 'services' in props:
                        service = ServiceGroup(subservice)
                        service.fromdict(props)
                    else:
                        service = Service(subservice)
                        service.fromdict(props)

                    # Link the group and its new subservice together
                    self._subservices[subservice] = service
                    service.parent = self

                    wrap.source = service
                    dep_mapping[subservice] = wrap

            # Generate dependency links of the service
            for wrap in dep_mapping.values():
                # Not any dependencies so just attach
                for dtype in wrap.deps:
                    for dep in wrap.deps[dtype]:
                        wrap.source.add_dep(self._subservices[dep],
                                                         sgth=dtype.upper())

            # Bind subgraph to the service group
            for service in self.iter_subservices():
                if not service.children:
                    service.add_dep(self._source, parent=False)
                    # Generate fake actions
                    for action in service._actions:
                        if action not in self._source._actions:
                            self._source.add_action(
                                Action(action, delay=0.01))
                if not service.parents:
                    service.add_dep(self._sink)
                    for action in service._actions:
                        if action not in self._sink._actions:
                            self._sink.add_action(
                                Action(action, delay=0.01))

        for subser in self.iter_subservices():
            subser.inherits_from(self)


class DepWrapper(object):
    '''
    Tool class allowing us to wrap the dependencies of a service. This
    class is used by the factory in order to provide an easiest way to
    to deal with dependencies.
    '''

    def __init__(self):
        self.source = None
        self.deps = {'require': [], 'require_weak': [], 'check': []}
