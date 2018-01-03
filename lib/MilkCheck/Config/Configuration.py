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

"""
Helpers for loading configuration files.
"""

import re
import os
import os.path
import yaml

class ConfigurationError(Exception):
    """Generic error for configuration rule file content error."""

def _merge_flow(flow):
    """Build and return only one dict from various streams."""
    merged = {}
    for data in flow:
        if not data:
            continue
        for elem, subelems in data.items():

            # Compat with old-style syntax, using 'service' at top scope
            if elem == 'service':
                name = subelems.pop('name')
                subelems = {name: subelems}
                elem = 'services'

            if elem in ('services', 'variables'):
                merged.setdefault(elem, {})
                merged[elem].update(subelems)
            else:
                raise ConfigurationError("Bad rule '%s'" % elem)
    return merged

def load_from_stream(stream):
    """
    Load configuration from a stream.

    A stream could be a string or file descriptor
    """
    return _merge_flow(yaml.safe_load_all(stream))

def load_from_dir(directory, recursive=False):
    """
    Load all YAML files in the provided directory.

    There is no recursion by default.
    """
    if not os.path.isdir(directory):
        raise ValueError("Invalid directory '%s'" % directory)

    flow = []
    for root, dirs, names in os.walk(directory):
        if not recursive:
            dirs[:] = []
        for name in names:
            fullname = os.path.join(root, name)
            if os.path.isfile(fullname) and re.search(r'\.ya?ml$', name):
                flow.append(load_from_stream(open(fullname)))

    return _merge_flow(flow)
