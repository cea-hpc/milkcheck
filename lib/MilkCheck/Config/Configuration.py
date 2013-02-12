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

'''
This module contains the
'''

import re
import yaml
from os import listdir
from os.path import walk, isdir
from os.path import isfile

from MilkCheck.ServiceManager import service_manager_self
from MilkCheck.Engine.Service import Service
from MilkCheck.Engine.ServiceGroup import ServiceGroup, DepWrapper

class MilkCheckConfig(object):
    '''
    This class load the configuration files located within the specified
    directory
    '''
    def __init__(self):
        self._flow = []

    def _go_through(self, _arg, dirname=None, names=None):
        '''List the files in dirname'''
        for my_file in names:
            if isfile('%s/%s' %(dirname, my_file)) and \
                re.match('^[\w]*\.(yaml|yml)$', my_file):
                self.load_from_stream(
                    open('%s/%s' % (dirname, my_file),'r'))

    def load_from_dir(self, directory=None, recursive=False):
        '''
        Load configuration files located within a directory. This method
        will go though the overall file hierarchy.
        '''
        if directory and isdir(directory):
            if recursive:
                walk(directory, self._go_through, None)
            else:
                self._go_through(None, dirname=directory,
                    names=listdir(directory))
        else:
            raise ValueError("Invalid directory '%s'" % directory)

    def load_from_stream(self, stream):
        '''
        Load configuration from a stream. A stream could be a string or
        file descriptor
        '''
        # removes empty statement.
        content = [item for item in yaml.safe_load_all(stream) if item]
        if content:
            self._flow.extend(content)

    def build_graph(self):
        '''
        Build the graph from the content found in self._flow. It is required to
        call load methods before to call this one. If so self._flow will remain
        empty.
        '''
        if self._flow:
            self._build_services()

    def _build_services(self):
        '''
        Instanciate services, variables and service group. This methods
        also populate the service manager.
        '''
        # Get back the manager
        manager = service_manager_self()
        dependencies = {}

        # Go through data registred within flow
        for data in self._flow:
            for elem, subelems in data.items():
                # Parse variables
                if elem == 'variables':
                    for (varname, value) in subelems.items():
                        # Variables could have been already defined on command
                        # line through defines, and they have priority.
                        # If several 'variables' section are defined, the first
                        # ones will have priority, and it is fine are there is
                        # no ordering guarantee.
                        if varname not in manager.variables:
                            manager.add_var(varname, value)
                # Parse service
                elif elem == 'service' and 'actions' in subelems:
                    ser = Service(subelems['name'])
                    ser.fromdict(subelems)
                    wrap = self._parse_deps(subelems)
                    wrap.source = ser
                    dependencies[ser.name] = wrap
                # Parse service group
                elif elem == 'service' and 'services' in subelems:
                    ser = ServiceGroup(subelems['name'])
                    ser.fromdict(subelems)
                    wrap = self._parse_deps(subelems)
                    wrap.source = ser
                    dependencies[ser.name] = wrap
                # Support for new style syntax to declare services
                # This is a simple mode, for compatibility, with old-style
                # syntax.
                elif elem == 'services':
                    grp = ServiceGroup('ALL')
                    grp.fromdict({elem: subelems})
                    for subservice in grp.iter_subservices():
                        # Dependencies are already handled inside the service
                        # group.
                        # This code is only here for compat (see below), to
                        # list all services which should be registered in
                        # ServiceManager.  When compat will be dropped, this
                        # will be simplified.
                        subservice.parent = None
                        wrap = DepWrapper()
                        wrap.source = subservice
                        dependencies[subservice.name] = wrap
                    # Services should be untied to its fake service group.
                    for svc in grp._source.parents.values():
                        svc.target.remove_dep('source')
                    for svc in grp._sink.children.values():
                        svc.target.remove_dep('sink', parent=True)
                else:
                    # XXX: Raise an exception with a better error handling
                    raise KeyError("Bad declaration of: %s" % elem)

        # Build relations between services
        for wrap in dependencies.values():
            for (dtype, values) in wrap.deps.items():
                for dep in values:
                    wrap.source.add_dep(
                        target=dependencies[dep].source, sgth=dtype.upper())
        # Populate the manager and set up inheritance
        for wrap in dependencies.values():
            manager.register_service(wrap.source)

    @classmethod
    def _parse_deps(cls, data):
        '''Return a DepWrapper containing the different types of dependencies'''
        wrap = DepWrapper()
        # This does not support 'before' alias for require_weak.
        # Only in new style configuration
        for content in ('require', 'require_weak', 'check'):
            if content in data:
                if type(data[content]) is str:
                    wrap.deps[content] = [ data[content] ]
                else:
                    wrap.deps[content] = data[content]
        return wrap

    def get_data_flow(self):
        '''Get parsed data'''
        return self._flow

    data_flow = property(fget=get_data_flow)
