#coding=utf-8
#copyright CEA (2011)  
#contributor: TATIBOUET Jérémie <tatibouetj@ocre.cea.fr>

"""
This module contains the ServiceManager class definition
"""

from MilkCheck.Engine.Service import Service
from MilkCheck.Engine.BaseService import ServiceNotFoundError
from MilkCheck.Engine.Action import Action
from ClusterShell.NodeSet import NodeSet

class ServiceManager(object):
    """
    The service manager has to handle call to services. It implements
    features allowing us to get dependencies of service and so son
    """
    
    def __init__(self):
        """
        ServiceManager constructor
        """
        
        #Services handled by the manager
        self._services = {}
        
        #Variables declared in the global scope
        self._variables = {}
        
        self._mock_init()
        
    def _mock_init(self):
        """
        Instancitates services and actions in order to test the engine
        """
        
        #Service Arthemis is declared here
        arth = Service("arthemis")
        arth.desc = "retrieves list of processes"
        arth.target = NodeSet("aury[11-12]")
        
        arth_start = Action("start")
        arth_start.command = "ps -el"
        
        arth_stop = Action("stop")
        arth_stop.command = "echo 'Arthemis is gonna stop'"
    
        arth.add_action(arth_start)
        arth.add_action(arth_stop)
        
        #Service Chiva is declared here
        chiva = Service("chiva")
        chiva.desc = "List all entities of the current directory"
        chiva.target = NodeSet("aury[11-12]")
        
        chiva_start = Action("start")
        chiva_start.command = "ps -el"
        
        chiva_stop = Action("stop")
        chiva_stop.command = "echo 'Chiva is gonna stop'"
    
        chiva.add_action(chiva_start)
        chiva.add_action(chiva_stop)
        
        chiva.add_dependency(arth)
        
        #Service Dyonisos is declared here
        dion = Service("dionysos")
        dion.desc = "Perform tree on directory specified"
        dion.target = NodeSet("aury13")
        
        dion_start = Action("start")
        dion_start.command = "tree /sbin/service"
        
        dion_stop = Action("stop")
        dion_stop.command = "Dyonisos is gonna stop"
        
        dion.add_action(dion_stop)
        dion.add_action(dion_start)
        
        dion.add_dependency(arth)
        
        #Service Brutus is declared here
        brut = Service("brutus")
        brut.desc = "Wanna sleep all the time"
        brut.target = NodeSet("aury[21,12,26]")
        
        brut_start = Action("start")
        brut_start.command = "sleep 15"
    
        brut_stop = Action("stop")
        brut_stop.command = "pids=$(pgrep sleep) | kill $pids"
        
        brut.add_action(brut_start)
        brut.add_action(brut_stop)
        
        brut.add_dependency(chiva)
        brut.add_dependency(dion)
        
        #Adds services into the main list
        self._services[arth.name] = arth 
        self._services[chiva.name] = chiva
        self._services[dion.name] = dion
        self._services[brut.name] = brut
        
    def call_services(self, services_names, action_name, params=None):
        """
        Allow the user to call one or multiple services
        """
        for name in services_names:
            service = None
            normalized_name = name.lower()
            if self._services.has_key(normalized_name) is True:
                service = self._services[normalized_name]
                service.run(action_name)
            else:
                raise ServiceNotFoundError()