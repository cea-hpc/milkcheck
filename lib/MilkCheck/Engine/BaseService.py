#
# Copyright CEA (2011-2012)
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
This module contains the definition of the Base class of a service and the
defnition of the different states that a service can go through
"""

# Classes
from MilkCheck.Engine.BaseEntity import BaseEntity
from MilkCheck.ActionManager import action_manager_self

class BaseService(BaseEntity):
    '''
    This abstract class defines the concept of service. A Service might be
    a node of graph because it inherit from the properties and methods of
    BaseEntity. BaseService basically defines the main methods that derived
    Services types have to implements.
    '''
    
    def __init__(self, name, target=None):
        BaseEntity.__init__(self, name, target)
        
        # Define a flag allowing us to specify that this service
        # is the original caller so we do not have to start his
        # children 
        self.origin = False

        # Used for ghost services or services that you do not want to execute
        self.simulate = False

    def reset(self):
        '''Reset values of attributes in order to perform multiple exec'''
        BaseEntity.reset(self)
        self.origin = False

    def run(self, action_name):
        '''Run an action over a service'''
        
        # A service using run become the calling point
        self.origin = True
        
        # Prepare the service and start the master task
        self.prepare(action_name)
        action_manager_self().run()
        
    def prepare(self, action_name=None):
        '''
        Recursive method allowing to prepare a service before his execution.
        The preparation of a service consist in checking that all of the
        dependencies linked to this service were solved. As soon as possible
        action requested will be started.
        '''
        raise NotImplementedError

    def update_status(self, status):
        '''
        Update the current service's status and whether all of his parents
        dependencies are solved start children dependencies.
        '''
        raise NotImplementedError
