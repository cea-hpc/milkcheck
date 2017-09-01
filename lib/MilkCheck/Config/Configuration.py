#
# Copyright CEA (2011-2017)
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

from ClusterShell.NodeSet import NodeSet

from MilkCheck.ServiceManager import service_manager_self
from MilkCheck.Engine.BaseEntity import UnknownDependencyError
from MilkCheck.Engine.Service import Service
from MilkCheck.Engine.ServiceGroup import ServiceGroup, DepWrapper

class ConfigurationError(Exception):
    """Generic error for configuration rule file content error."""

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

        # We need to parse variables first to be sure that variables used
        # in services are already parsed (see #15)
        for data in self._flow:
            # Parse variables
            if 'variables' in data:
                for varname, value in data['variables'].items():
                    if varname not in manager.variables:
                        manager.add_var(varname, value)

        # Go through data registred within flow
        for data in self._flow:
            for elem, subelems in data.items():
                # Parse service
                if elem == 'service' and 'actions' in subelems:
                    ser = Service(subelems['name'])
                    ser.fromdict(subelems)
                    wrap = self._parse_deps(subelems, ser)
                    wrap.source = ser
                    dependencies[ser.name] = wrap
                # Parse service group
                elif elem == 'service' and 'services' in subelems:
                    ser = ServiceGroup(subelems['name'])
                    ser.fromdict(subelems)
                    wrap = self._parse_deps(subelems, ser)
                    wrap.source = ser
                    dependencies[ser.name] = wrap
                # Support for new style syntax to declare services
                # This is a simple mode, for compatibility, with old-style
                # syntax.
                elif elem == 'services':
                    for names, props in subelems.items():
                        for svcname in NodeSet(names):

                            service = None
                            if 'services' in props:
                                service = ServiceGroup(svcname)
                            else:
                                service = Service(svcname)

                            service.fromdict(props)
                            wrap = self._parse_deps(props, service)
                            wrap.source = service
                            dependencies[service.name] = wrap

                elif elem != 'variables':
                    raise ConfigurationError("Bad rule '%s'" % elem)

        # Build relations between services
        for wrap in dependencies.values():
            for (dtype, values) in wrap.deps.items():
                for dep in values:
                    if dep not in dependencies:
                        raise UnknownDependencyError(dep)
                    wrap.source.add_dep(
                        target=dependencies[dep].source, sgth=dtype.upper())
        # Populate the manager and set up inheritance
        for wrap in dependencies.values():
            manager.register_service(wrap.source)
            wrap.source.resolve_all()

    @classmethod
    def _parse_deps(cls, data, service=None):
        '''Return a DepWrapper containing the different types of dependencies'''
        wrap = DepWrapper()
        for content in ('require', 'require_weak', 'require_filter', 'filter',
                        'check', 'before', 'after'):
            if content in data:
                if service is not None:
                    data[content] = service._resolve(data[content])
                if content in ('before', 'after'):
                    data['require_weak'] = data[content]
                    content = 'require_weak'
                # Only for compat with v1.1beta versions
                if content == 'require_filter':
                    data['filter'] = data[content]
                    content = 'filter'
                if type(data[content]) is str:
                    wrap.deps[content] = [ data[content] ]
                else:
                    wrap.deps[content] = data[content]
        return wrap

    def get_data_flow(self):
        '''Get parsed data'''
        return self._flow

    data_flow = property(fget=get_data_flow)
