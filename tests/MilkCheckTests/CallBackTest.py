# Copyright CEA (2011)
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

'''
This module defines the tests cases targeting the CallBackHandler.
'''

# Classes
from unittest import TestCase

# Symbols
from MilkCheck.Callback import CallbackHandler, call_back_self
from MilkCheck.Callback import EV_STARTED

class CallBackHandlerTest(TestCase):
    '''
    Tests cases of CallBackHandler
    '''
    def test_instanciation(self):
        '''Test the instanciation of a CallBackHandler'''
        self.assertTrue(CallbackHandler())
        self.assertTrue(call_back_self())
        self.assertTrue(call_back_self() is call_back_self())
        CallbackHandler._instance = None

    def test_attach_interface(self):
        '''Test ability to attach interface to the handler'''
        chandler = call_back_self()
        obj = object()
        chandler.attach(obj)
        self.assertTrue(obj in chandler._interfaces)
        CallbackHandler._instance = None

    def test_detach_interface(self):
        '''Test ability to detach interface from the handler'''
        chandler = call_back_self()
        obj = object()
        chandler.attach(obj)
        chandler.detach(obj)
        self.assertTrue(obj not in chandler._interfaces)
        CallbackHandler._instance = None