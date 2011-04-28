# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This is the entry point of the program
"""

import sys
sys.path.insert(0,"/cea/home/gpocre/tatibouetj/internship/prod/code/lib")

from MilkCheck.ServiceManager import ServiceManager
from MilkCheck.Config.Configuration import Configuration

if __name__ == "__main__":

    manager = ServiceManager()
    manager.call_services(["brutus"],"start")
