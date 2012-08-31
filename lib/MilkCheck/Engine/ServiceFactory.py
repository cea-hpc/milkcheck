# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This module contains the ServiceFactory class definition
"""

from ClusterShell.NodeSet import NodeSet

from MilkCheck.Engine.Service import Service
from MilkCheck.Engine.ServiceGroup import ServiceGroup
from MilkCheck.Engine.Action import Action
from MilkCheck.Engine.ActionFactory import ActionFactory

class ServiceFactory(object):
    """
    This class allow us to build a Service or ServiceGroup thanks
    to a dictionnary.
    """
    @staticmethod
    def create_minimal_service(name, target=None):
        '''Build a minimal service object and return it.'''
        return Service(name, target)

    @staticmethod
    def create_service(name, desc=None, target=None, fanout=None, errors=None,
        origin=False, simulate=False):
        '''Build an object Service from the parameters and return it.'''
        ser = Service(name, target)
        ser.desc = desc
        ser.fanout = fanout
        ser.errors = errors
        ser.origin = origin
        ser.simulate = simulate
        return ser

    @staticmethod
    def create_service_from_dict(serialized_service):
        '''Build an object service from a dictionnary and return it.'''
        service = serialized_service['service']
        ser = Service(service['name'])
        # Creation of the service
        for item in service:
            if item == 'target':
                ser.target = service[item]
                ser.target_backup = service[item]
            elif item == 'mode':
                ser.mode = service[item]
            elif item == 'fanout':
                ser.fanout = service[item]
            elif item == 'timeout':
                ser.timeout = service[item]
            elif item == 'errors':
                ser.errors = service[item]
            elif item == 'desc':
                ser.desc = service[item]
            elif item == 'variables':
                for (varname, value) in service[item].items():
                    ser.add_var(varname, value)
            elif item == 'actions':
                dependencies = {}
                actions = {}
                for names, props in service[item].items():
                    for action in NodeSet(names):
                        actions[action] = \
                                ActionFactory.create_action_from_dict(
                                    {action: props})
                        dependencies[action] = props.get('check', [])

                for action in actions.values():
                    for dep in dependencies[action.name]:
                        action.add_dep(actions[dep])
                    ser.add_action(action)

        # Inherits properies between service and actions
        for action in ser.iter_actions():
            action.inherits_from(ser)

        return ser


class ServiceGroupFactory(object):
    '''This class defines the factory of ServiceGroup objects'''

    @staticmethod
    def create_servicegroup(name, target=None):
        '''Instanciate a ServiceGroup from parameters'''
        return ServiceGroup(name, target)

    @staticmethod
    def create_servicegroup_from_dict(serialized_sgrp):
        '''Instanciate a ServiceGroup from a dictionnary'''
        ser = serialized_sgrp['service']
        sergrp = ServiceGroup(ser['name'])
        for item in ser:
            if item == 'target':
                sergrp.target = ser[item]
                sergrp.target_backup = ser[item]
            elif item == 'fanout':
                sergrp.fanout = ser[item]
            elif item == 'timeout':
                sergrp.timeout = ser[item]
            elif item == 'errors':
                sergrp.errors = ser[item]
            elif item == 'desc':
                sergrp.desc = ser[item]
            elif item == 'variables':
                for (varname, value) in ser[item].items():
                    sergrp.add_var(varname, value)
            elif item == 'services':
                dep_mapping = {}

                # Wrap dependencies from YAML and build the service
                for names, props in ser['services'].items():
                    for subservice in NodeSet(names):
                        # Parsing dependencies
                        wrap = DepWrapper()
                        for prop in ('require', 'require_weak', 'check'):
                            if prop in props:
                                wrap.deps[prop] = props[prop]

                        # Get subservices which might be Service or ServiceGroup
                        props['name'] = subservice
                        service = None
                        if 'services' in props:
                            service = \
                              ServiceGroupFactory.create_servicegroup_from_dict(
                                                             {'service': props})
                        else:
                            service = ServiceFactory.create_service_from_dict(
                                                             {'service': props})
                        sergrp._subservices[subservice] = service
                        wrap.source = service
                        dep_mapping[subservice] = wrap

                # Generate dependency links of the service
                for wrap in dep_mapping.values():
                    # Not any dependencies so just attach 
                    for dtype in wrap.deps:
                        for dep in wrap.deps[dtype]:
                            wrap.source.add_dep(sergrp._subservices[dep],
                                                             sgth=dtype.upper())

                # Bind subgraph to the service group
                for service in sergrp._subservices.values():
                    service.parent = sergrp
                    if not service.children:
                        service.add_dep(sergrp._source, parent=False)
                        # Generate fake actions
                        for action in service._actions:
                            if not sergrp.has_action(action):
                                sergrp._source.add_action(
                                    Action(action, delay=0.01))
                    if not service.parents:
                        service.add_dep(sergrp._sink)
                        for action in service._actions:
                            if not sergrp.has_action(action):
                                sergrp._sink.add_action(
                                    Action(action, delay=0.01))
        for subser in sergrp.iter_subservices():
            subser.inherits_from(sergrp)
        return sergrp

class DepWrapper(object):
    '''
    Tool class allowing us to wrap the dependencies of a service. This
    class is used by the factory in order to provide an easiest way to
    to deal with dependencies.
    '''

    def __init__(self):
        self.source = None
        self.deps = {'require': [], 'require_weak': [], 'check': []}

    def is_empty(self):
        '''
        Is the dependency wrapper empty. It returns true if not any list
        contain at least one element
        '''
        return not self.deps['require'] and not self.deps['require_weak'] and \
            not self.deps['check']
