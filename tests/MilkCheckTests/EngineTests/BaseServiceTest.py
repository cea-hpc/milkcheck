# coding=utf-8
# Copyright CEA (2011) 
# Contributor: TATIBOUET Jérémie <tatibouetj@ocre.cea.fr>

"""
This modules defines the tests cases targeting the BaseService
"""
import sys
from exceptions import TypeError
from unittest import TestCase

from MilkCheck.Engine.BaseService import BaseService
from MilkCheck.Engine.BaseService import IllegalDependencyIdentifier
from MilkCheck.Engine.BaseService import IN_PROGRESS, SUCCESS, NO_STATUS
from MilkCheck.Engine.Service import Service

class BaseServiceTest(TestCase):
    """
    tests cases for the class BaseService
    """
    
    def setUp(self):
        self._service = Service("test_service")
    
    def test_is_require_dep(self):
       """test the mehtod is_require_dep"""
       self._service.cleanup_dependencies()
       serv_a = Service("A")
       serv_b = Service("B")
       self._service.add_dependency(serv_a)
       self._service.add_dependency(serv_b,"check")
       self.assert_(
            self._service.is_require_dep(serv_a),
                "should be true")
       self.assert_(
            not self._service.is_require_dep(serv_b),
                "should be false")
                
    def test_is_check_dep(self):
       self._service.cleanup_dependencies()
       serv_a = Service("A")
       serv_b = Service("B")
       self._service.add_dependency(serv_a)
       self._service.add_dependency(serv_b,"check")
       self.assert_(
            not self._service.is_check_dep(serv_a),
                "should be false")
       self.assert_(
            self._service.is_check_dep(serv_b),
                "should be true")
       
    def test_add_dependency(self):
        """test the method add depedency"""
        # require depedency
        self._service.cleanup_dependencies()
        rdep = Service("dep1")
        self._service.add_dependency(rdep)
        self.assert_(
            self._service.is_require_dep(rdep),
                "should be a require dependency")
        
        # check dependency
        cdep = Service("dep2")
        self._service.add_dependency(cdep,"check")
        self.assert_(
            self._service.is_check_dep(cdep),
                "should be a check dependency")
                
        # dependency with a None Service
        none_except = False
        try:
            self._service.add_dependency(None)
        except TypeError:
            none_except = True
        self.assert_(none_except, 
            "should raise an exception because service is None")
            
        # depdency with bad name identifier
        none_except = False
        try:
            self._service.add_dependency(Service("dep3"),"hello")
        except IllegalDependencyIdentifier:
            none_except = True
        self.assert_(none_except, 
            "should raise an exception dependency identifier is illegal")
        
    def test_remaining_dependencies(self):
        """test the method remaining dependencies"""
        self._service.cleanup_dependencies()
        serv_a = Service("A")
        serv_b = Service("B")
        self._service.add_dependency(serv_a)
        self._service.add_dependency(serv_b,"check")
        deps = self._service._remaining_dependencies()
        
        self.assert_(len(deps) == 2, "should have two dependencies")
        self.assert_(serv_a.name == deps[0][0].name, "A should be in")
        self.assert_(serv_b.name == deps[1][0].name, "B should be in")
        
        self._service.cleanup_dependencies()
        
        serv_a.status = IN_PROGRESS
        self._service.add_dependency(serv_a)
        self._service.add_dependency(serv_b,"check")
        deps = self._service._remaining_dependencies()
        self.assert_(len(deps) == 1, "should have one dependencies")
        self.assert_(serv_b.name == deps[0][0].name, "B should be in")

    def test_update_status(self):
        
        self._service.cleanup_dependencies()
        
        #Test status updated
        self._service.update_status(IN_PROGRESS)
        self.assert_(self._service.status == IN_PROGRESS)
        self._service.status = NO_STATUS
        
        """
        There is a dependency between test_service and A. As soon as
        test_service does a prepare() A status must be modified to
        IN_PROGRESS
        """
        serv_a = Service("A")
        self._service.add_dependency(serv_a)
#        self._service.prepare()
#        self._assert(serv_a.status == IN_PROGRESS, "A must be IN_PROGRESS")
        
    def tearDown(self):
        del self._service
