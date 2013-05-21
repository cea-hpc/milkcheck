# Copyright CEA (2011-2013)
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

'''
This module defines the tests cases targeting the CallBackHandler.
'''

# Classes
from unittest import TestCase
from MilkCheck.Callback import CallbackHandler, call_back_self, CoreEvent

# Symbols
from MilkCheck.Callback import EV_STARTED, EV_COMPLETE, EV_STATUS_CHANGED
from MilkCheck.Callback import EV_TRIGGER_DEP, EV_FINISHED, EV_DELAYED

class EventTest(CoreEvent):
    '''
    Class test to manage recieved events
    '''
    def __init__(self):
        '''Init last_event to gather the recieved event type'''
        CoreEvent.__init__(self)
        self.last_event = None
        call_back_self().attach(self)

    def ev_started(self, obj):
        '''Event triggered when recieve EV_STARTED'''
        self.last_event = EV_STARTED

    def ev_complete(self, obj):
        '''Event triggered when recieve EV_COMPLETE'''
        self.last_event = EV_COMPLETE

    def ev_status_changed(self, obj):
        '''Event triggered when recieve EV_STATUS_CHANGED'''
        self.last_event = EV_STATUS_CHANGED

    def ev_delayed(self, obj):
        '''Event triggered when recieve EV_DELAYED'''
        self.last_event = EV_DELAYED

    def ev_trigger_dep(self, obj_source, obj_triggered):
        '''Event triggered when recieve EV_TRIGGER_DEP'''
        self.last_event = EV_TRIGGER_DEP

    def ev_finished(self, obj):
        '''Event triggered when recieve EV_FINISHED'''
        self.last_event = EV_FINISHED

class CallBackHandlerTest(TestCase):
    '''
    Tests cases of CallBackHandler
    '''
    def tearDown(self):
        '''Restore CallbackHandler'''
        CallbackHandler._instance = None

    def test_instanciation(self):
        '''Test the instanciation of a CallBackHandler'''
        self.assertTrue(CallbackHandler())
        self.assertTrue(call_back_self())
        self.assertTrue(call_back_self() is call_back_self())

    def test_attach_interface(self):
        '''Test ability to attach interface to the handler'''
        chandler = call_back_self()
        obj = object()
        chandler.attach(obj)
        self.assertTrue(obj in chandler._interfaces)

    def test_detach_interface(self):
        '''Test ability to detach interface from the handler'''
        chandler = call_back_self()
        obj = object()
        chandler.attach(obj)
        chandler.detach(obj)
        self.assertTrue(obj not in chandler._interfaces)

    def test_notify_interface(self):
        '''Test notification on event type'''
        event = EventTest()
        for evname in (EV_STARTED, EV_COMPLETE, EV_STATUS_CHANGED,
                       EV_FINISHED, EV_DELAYED):
            call_back_self().notify(None, evname)
            self.assertEqual(event.last_event, evname)

        # EV_TRIGGER_DEP need a tuple as object parameter
        evname = EV_TRIGGER_DEP
        call_back_self().notify((None, None), EV_TRIGGER_DEP)
        self.assertEqual(event.last_event, evname)

    def test_notimplemented(self):
        '''Test NotImplementedError'''
        result = []
        event = CoreEvent()
        call_back_self().attach(event)
        events = [EV_STARTED,        EV_COMPLETE,
                  EV_STATUS_CHANGED, EV_FINISHED,
                  EV_TRIGGER_DEP, EV_DELAYED]
        for evname in events:
            try:
                # Need a tuple as first arg to bypass assert for EV_DELAYED
                # in call_back_self().notify()
                call_back_self().notify((None, None), evname)
            except NotImplementedError:
                result.append(evname)

        self.assertEqual(len(events), len(result),
                "%s should raise NotImplementedError" %
                        list(set(events) - set(result) ))
