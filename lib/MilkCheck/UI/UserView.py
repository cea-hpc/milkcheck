# Copyright CEA (2011)
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

'''
This module contains the UserView class definition.
'''

from MilkCheck.Callback import CoreEvent
from MilkCheck.Callback import CallbackHandler, call_back_self

# Definition of retcodes
RC_OK = 0
RC_WARNING = 3
RC_ERROR = 6
RC_EXCEPTION = 9
RC_UNKNOWN_EXCEPTION = 12 

class UserView(CoreEvent):
    '''
    This class models the operation that can be performed from the User
    point of view. This class is abstract and implements EngineNotification
    which help her to get back stream of informations from the Engine.
    '''
    def __init__(self):
        '''
        The UserView object is automatically attached to the callback handler
        in order to receive events from the core.
        '''
        call_back_self().attach(self)