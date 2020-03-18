# Copyright CEA (2011-2019)
# Contributor: CEDEYN Aurelien
#
"""
Define common function for MilkCheck tests
"""

import tempfile
import textwrap
from ClusterShell.Task import task_self

def setup_sshconfig():
    """ Generate a custom ssh configuration for tests """
    ssh_cfg = tempfile.NamedTemporaryFile()
    # Create a ssh_config file to manage timeout
    # Get first default configuration
    with (open('/etc/ssh/ssh_config', 'r')) as dflt_ssh_cfg:
        ssh_cfg.write(dflt_ssh_cfg.read().encode())
        dflt_ssh_cfg.close()
    # Add custom configuration
    ssh_cfg.write(textwrap.dedent("""
                              Host *
                                  UserKnownHostsFile /dev/null
                                  StrictHostKeyChecking no
                                  CheckHostIP no
                                  LogLevel ERROR
                              Host timeout
                                  proxycommand sleep 3
                                      """).encode())
    ssh_cfg.flush()
    task = task_self()
    task.set_info('ssh_options', '-F {0}'.format(ssh_cfg.name))
    return ssh_cfg


def cleanup_sshconfig(ssh_cfg):
    """ Remove ssh configuration file and restore task options """
    ssh_cfg.close()
    task = task_self()
    task.set_info('ssh_options', '')
