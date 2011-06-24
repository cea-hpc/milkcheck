# Copyright CEA (2011)
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This module contains the ActionFactory class definition
"""

from MilkCheck.Engine.Action import Action

class ActionFactory(object):
    '''
    This class defines static method allowing the user to build Action objects
    in using diffrent profiles.
    '''

    @staticmethod
    def create_action(name, target=None, command=None, timeout=0, delay=0):
        return Action(name, target, command, timeout, delay)
        
    @staticmethod
    def create_action_from_dict(serialized_act):
        name = serialized_act.iterkeys().next()
        action = Action(name)
        if 'delay' in serialized_act[name]:
           action.delay = serialized_act[name]['delay'] 
        for item in serialized_act[name]:
            if item == 'target':
                action.target = serialized_act[name][item]
                action.target_backup = action.target
            elif item == 'cmd':
                action.command = serialized_act[name][item]
            elif item == 'timeout':
                action.timeout = serialized_act[name][item]
            elif item == 'errors':
                action.errors = serialized_act[name][item]
            elif item == 'fanout':
                action.fanout = serialized_act[name][item]
            elif item == 'retry':
                action.retry = serialized_act[name][item]
            elif item == 'variables':
                for (varname, value) in serialized_act[name][item].items():
                    action.add_var(varname, value)
        return action