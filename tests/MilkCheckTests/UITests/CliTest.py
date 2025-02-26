# Copyright CEA (2011-2019)
# Contributor: TATIBOUET Jeremie
# Contributor: CEDEYN Aurelien
#

"""
This modules defines the tests cases targeting the class CommandLine
"""

import os
import re
import select
import socket
import sys
import time
import tempfile
import textwrap
try:
    from StringIO import StringIO
except ImportError:
    # Python 3 new name
    from io import StringIO

from unittest import TestCase

import MilkCheck.UI.Cli
from MilkCheck.UI.Cli import CommandLine, ConsoleDisplay, MAXTERMWIDTH
from MilkCheck.ServiceManager import ServiceManager
from MilkCheck.Engine.Service import Service
from MilkCheck.Engine.Action import Action, ActionManager
from MilkCheck.Engine.ServiceGroup import ServiceGroup
from MilkCheck.Callback import CallbackHandler
from MilkCheck.config import ConfigParser
from ClusterShell.NodeSet import NodeSet

# Symbols
from MilkCheck.UI.Cli import RC_OK, RC_ERROR, RC_EXCEPTION, \
                             RC_UNKNOWN_EXCEPTION, RC_WARNING
from MilkCheck.Engine.BaseEntity import REQUIRE_WEAK

# Exceptions
from yaml.scanner import ScannerError
from signal import SIGINT
from MilkCheck.Engine.Service import ActionNotFoundError
from MilkCheck.UI.OptionParser import InvalidOptionError

# SSH setup
from MilkCheckTests import setup_sshconfig, cleanup_sshconfig

HOSTNAME = socket.gethostname().split('.')[0]
PROGNAME = os.path.basename(sys.argv[0])

class MyOutput(StringIO):
    ''' Class replacing stdout to manage output in nosetest '''

    def write(self, line):
        ''' Writes a word per line'''

        # Format help usage
        line = re.sub('^usage: ', 'Usage: ', line)
        line = re.sub('\noptions:\n', '\nOptions:\n', line)

        # Clear secounds elapsed
        line = re.sub(r' [0-9]+\.[0-9]+ s', ' 0.00 s', line)
        # All time related to midnight
        line = re.sub(r'\[[0-9]{2}:[0-9]{2}:[0-9]{2}\] ', '[00:00:00] ', line)
        # Replace local hostname by "HOSTNAME"
        line = re.sub(HOSTNAME, 'HOSTNAME', line)

        # SSH output is different with OpenSSH (4.x ?)
        # We modify the output to match those from OpenSSH 5.x
        line = re.sub(r'ssh: (\w+): (Name or service not known)',
                      'ssh: Could not resolve hostname \\1: \\2', line)
        line = re.sub(r'ssh: (\w+): (Temporary failure in name resolution)',
                      'ssh: Could not resolve hostname \\1: \\2', line)

        # SSH output is different with OpenSSH (>= 6.6)
        # The output gives a lower hostname, we convert it to lower case
        # by default
        def lower_hostname(match):
            return "ssh: Could not resolve hostname %s" % match.group(1).lower()
        line = re.sub(r'ssh: Could not resolve hostname (\w+):.*',
                      lower_hostname, line)

        # Traceback output doesn't need line number and source location
        line = re.sub(r'File .*, line .*, in (.*)',
                      'File "source.py", line 000, in \\1', line)
        StringIO.write(self, line)

class CLISimpleTest(TestCase):
    """ Class to test basic CLI invocation """

    def setUp(self):
        """ Define configuration file for simple tests """
        self.configdir = tempfile.mkdtemp(suffix='milktest')
        self.configfile = tempfile.NamedTemporaryFile(suffix='.yaml', dir=self.configdir)
        self.configfile.write(textwrap.dedent("""
                              services:
                                  basic:
                                      desc: 'Simple service declaration'
                                      actions:
                                          start:
                                              cmd: /bin/true""").encode())
        self.configfile.flush()

    def tearDown(self):
        """ Cleanup temporary file installed in setUp """
        self.configfile.close()
        os.rmdir(self.configdir)

    def _cli_check(self, args, retcode=RC_OK):
        """Simple wrapper to CLI execute()"""
        cli = CommandLine()
        rc = cli.execute(args + ['-c', self.configdir])
        # Check return code
        self.assertEqual(rc, retcode)

    def test_basic(self):
        """ Run basic CLI test """
        self._cli_check(['basic', 'start'])

    def test_graph(self):
        """ Run basic CLI --graph test """
        self._cli_check(['--graph'])

class CLICommon(TestCase):
    ''' Class to manage Cli in tests'''

    def setUp(self):
        ConfigParser.DEFAULT_FIELDS['config_dir']['value'] = ''
        ConfigParser.CONFIG_PATH = '/dev/null'

        self.manager = ServiceManager()
        ActionManager._instance = None

        # Setup stdout and stderr as a MyOutput file
        sys.stdout = MyOutput()
        sys.stderr = MyOutput()

        # Setup ssh configuration
        self.ssh_cfg = setup_sshconfig()

    def tearDown(self):
        '''Restore sys.stdout and sys.stderr'''
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        CallbackHandler._instance = None

        # Cleanup ssh configuration
        cleanup_sshconfig(self.ssh_cfg)

    def _output_check(self, args, retcode, outexpected,
                      errexpected=None, show_running=True, term_width=77):
        """
        Test Milcheck output with:
         - args: command line args for cli.execute
         - outexpected: expected std output
         - errexpected: optional expected stderr
         - show_running: True if we want to capture the running tasks
        """
        cli = CommandLine()
        cli.manager = self.manager
        cli._console.cleanup = False
        cli._console._term_width = term_width
        cli._console._show_running = show_running
        rc = cli.execute(args)

        # STDOUT
        msg = sys.stdout.getvalue()
        for expected, output in zip(outexpected.splitlines(), msg.splitlines()):
            self.assertEqual(expected, output)
        self.assertEqual(outexpected, msg)

        # STDERR
        if errexpected is not None:
            msg = sys.stderr.getvalue()
            for expected, output in zip(errexpected.splitlines(), msg.splitlines()):
                self.assertEqual(expected, output)
            self.assertEqual(errexpected, msg)

        # Check return code
        self.assertEqual(rc, retcode)


class CLIBigGraphTests(CLICommon):
    '''Tests cases of the command line interface'''

    def setUp(self):
        '''
        Set up the graph of services within the service manager

        Graph
                __ S2                    __ I1
            S1 /         -- G1 -- (src) /    ^  -- (sink)
               `-- S3 --/               `-- I2

        Each node has an action start and an action stop
        '''
        CLICommon.setUp(self)

        svc1 = Service('S1')
        svc1.desc = 'I am the service S1'
        self.svc2 = svc2 = Service('S2')
        svc2.desc = 'I am the service S2'
        svc3 = Service('S3')
        svc3.desc = 'I am the service S3'
        group1 = ServiceGroup('G1')
        inter1 = Service('I1')
        inter1.desc = 'I am the service I1'
        inter2 = Service('I2')
        inter2.desc = 'I am the service I2'

        # Actions S1
        start_svc1 = Action('start', HOSTNAME + ', BADNODE', '/bin/true')
        start_svc1.delay = 1
        stop_svc1 = Action('stop', HOSTNAME + ',BADNODE', '/bin/true')
        stop_svc1.delay = 1
        svc1.add_actions(start_svc1, stop_svc1)
        # Actions S2
        svc2.add_action(Action('start', HOSTNAME + ',BADNODE', '/bin/true'))
        svc2.add_action(Action('stop', HOSTNAME + ',BADNODE', '/bin/true'))
        # Actions S3
        svc3.add_action(Action('start', HOSTNAME + ',BADNODE', '/bin/false'))
        svc3.add_action(Action('stop', HOSTNAME + ',BADNODE', '/bin/false'))
        # Actions I1
        inter1.add_action(Action('start', HOSTNAME, 'echo ok'))
        inter1.add_action(Action('stop', HOSTNAME, 'echo ok'))
        # Actions I2
        inter2.add_action(Action('start', HOSTNAME + ',BADNODE', '/bin/true'))
        inter2.add_action(Action('stop', HOSTNAME + ',BADNODE', '/bin/true'))

        # Build graph
        svc1.add_dep(target=svc2)
        svc1.add_dep(target=svc3)
        svc3.add_dep(target=group1)
        inter2.add_dep(inter1)
        group1.add_inter_dep(target=inter1)
        group1.add_inter_dep(target=inter2)

        # Register services within the manager
        self.manager.add_service(svc1)
        self.manager.add_service(svc2)
        self.manager.add_service(svc3)
        self.manager.add_service(group1)

    def test_execute_std_verbosity(self):
        '''CLI execute() (no option)'''
        self._output_check(['S3', 'start'], RC_ERROR,
"""G1.I1 - I am the service I1                                       [    OK   ]
start G1.I2 ran in 0.00 s
 > BADNODE: ssh: Could not resolve hostname badnode
 > BADNODE exited with 255
G1.I2 - I am the service I2                                       [  ERROR  ]
G1                                                                [DEP_ERROR]
S3 - I am the service S3                                          [DEP_ERROR]
""")

    def test_execute_verbosity_1(self):
        '''CLI execute() (-v)'''
        self._output_check(['S3', 'start', '-v'], RC_ERROR,
"""start G1.I1 on HOSTNAME
 > echo ok
G1.I1 - I am the service I1                                       [    OK   ]
start G1.I2 on {}
 > /bin/true
start G1.I2 ran in 0.00 s
 > BADNODE: ssh: Could not resolve hostname badnode
 > HOSTNAME exited with 0
 > BADNODE exited with 255
G1.I2 - I am the service I2                                       [  ERROR  ]
G1                                                                [DEP_ERROR]
S3 - I am the service S3                                          [DEP_ERROR]
""".format(NodeSet('BADNODE,HOSTNAME')))

    def test_execute_verbosity_2(self):
        '''CLI execute() (-vv)'''
        self._output_check(['S3', 'start', '-vv'], RC_ERROR,
"""start G1.I1 on HOSTNAME
 > echo ok
start G1.I1 ran in 0.00 s
 > HOSTNAME: ok
 > HOSTNAME exited with 0
G1.I1 - I am the service I1                                       [    OK   ]
start G1.I2 on {}
 > /bin/true
start G1.I2 ran in 0.00 s
 > BADNODE: ssh: Could not resolve hostname badnode
 > HOSTNAME exited with 0
 > BADNODE exited with 255
G1.I2 - I am the service I2                                       [  ERROR  ]
G1                                                                [DEP_ERROR]
S3 - I am the service S3                                          [DEP_ERROR]
""".format(NodeSet('BADNODE,HOSTNAME')))

    def test_execute_debug(self):
        '''CLI execute() (-d)'''
        self._output_check(['S3', 'start', '-d'], RC_ERROR,
"""start G1.I1 on HOSTNAME
 > echo ok
start G1.I1 ran in 0.00 s
 > HOSTNAME: ok
 > HOSTNAME exited with 0
G1.I1 - I am the service I1                                       [    OK   ]
start G1.I2 on BADNODE,HOSTNAME
 > /bin/true
start G1.I2 ran in 0.00 s
 > BADNODE: ssh: Could not resolve hostname badnode
 > HOSTNAME exited with 0
 > BADNODE exited with 255
G1.I2 - I am the service I2                                       [  ERROR  ]
G1                                                                [DEP_ERROR]
S3 - I am the service S3                                          [DEP_ERROR]
""",
"""[00:00:00] DEBUG    - Configuration
assumeyes: False
config_dir: 
confirm_actions: []
dryrun: False
fanout: 64
nodeps: False
report: no
reverse_actions: ['stop']
summary: False
tags: {setoutput}
verbosity: 5
[I1]\r[I1]\r[I2]\r[I2]\r""".format(setoutput=str(set())))

    def test_excluded_node(self):
        '''Execute with a node exclusion (-vvv -x ...)'''
        self._output_check(['S3', 'stop', '-vvv', '-x', 'BADNODE'], RC_ERROR,
"""stop S1 will fire in 1 s
stop S1 on HOSTNAME
 > /bin/true
stop S1 ran in 0.00 s
 > HOSTNAME exited with 0
S1 - I am the service S1                                          [    OK   ]
stop S3 on HOSTNAME
 > /bin/false
stop S3 ran in 0.00 s
 > HOSTNAME exited with 1
S3 - I am the service S3                                          [  ERROR  ]
""")

    def test_selected_node(self):
        '''Execute with a limited node list (-vvv -n ...)'''
        self._output_check(['S3', 'start', '-d', '-n', HOSTNAME], RC_ERROR,
"""start G1.I1 on HOSTNAME
 > echo ok
start G1.I1 ran in 0.00 s
 > HOSTNAME: ok
 > HOSTNAME exited with 0
G1.I1 - I am the service I1                                       [    OK   ]
start G1.I2 on HOSTNAME
 > /bin/true
start G1.I2 ran in 0.00 s
 > HOSTNAME exited with 0
G1.I2 - I am the service I2                                       [    OK   ]
G1                                                                [    OK   ]
start S3 on HOSTNAME
 > /bin/false
start S3 ran in 0.00 s
 > HOSTNAME exited with 1
S3 - I am the service S3                                          [  ERROR  ]
""",
"""[00:00:00] DEBUG    - Configuration
assumeyes: False
config_dir: 
confirm_actions: []
dryrun: False
fanout: 64
nodeps: False
only_nodes: HOSTNAME
report: no
reverse_actions: ['stop']
summary: False
tags: {setoutput}
verbosity: 5
[I1]\r[I1]\r[I2]\r[I2]\r[S3]\r[S3]\r""".format(setoutput=str(set())))

    def test_execute_explicit_service(self):
        '''Execute a service from the CLI (-vvv -x ...)'''
        self._output_check(['G1', 'stop', '-vvv', '-x', 'BADNODE'], RC_ERROR,
"""stop S1 will fire in 1 s
stop S1 on HOSTNAME
 > /bin/true
stop S1 ran in 0.00 s
 > HOSTNAME exited with 0
S1 - I am the service S1                                          [    OK   ]
stop S3 on HOSTNAME
 > /bin/false
stop S3 ran in 0.00 s
 > HOSTNAME exited with 1
S3 - I am the service S3                                          [  ERROR  ]
G1                                                                [DEP_ERROR]
""")

    def test_execute_services_exclusion(self):
        '''CLI execute() (-X S3 -x ... -vvv)'''
        self._output_check(['S1', 'start', '-vvv', '-X', 'S3', '-x', 'BADNODE'],
                           RC_OK,
"""start S2 on HOSTNAME
 > /bin/true
start S2 ran in 0.00 s
 > HOSTNAME exited with 0
S2 - I am the service S2                                          [    OK   ]
start S1 will fire in 1 s                                                    
start S1 on HOSTNAME
 > /bin/true
start S1 ran in 0.00 s
 > HOSTNAME exited with 0
S1 - I am the service S1                                          [    OK   ]
""")

    def test_execute_retcode_exception(self):
        """CLI return '9' if a known exception is raised."""
        self._output_check(['badSVC', 'start'], RC_EXCEPTION, "",
                      """[00:00:00] ERROR    - Undefined service [badSVC]\n""")

    def test_execute_unknown_exception(self):
        """CLI return '12' if an unknown exception is raised."""
        self.manager.call_services = None
        self._output_check(['S2', 'start'], RC_UNKNOWN_EXCEPTION, "",
"""[00:00:00] ERROR    - Unexpected Exception : 'NoneType'"""\
""" object is not callable
""")

    def test_multiple_services(self):
        """CLI execute() with explicit services (S1 G1 -d)"""
        self._output_check(['S3', 'G1', 'start', '-d', '-x', 'BADNODE'],
                           RC_ERROR,
"""start G1.I1 on HOSTNAME
 > echo ok
start G1.I1 ran in 0.00 s
 > HOSTNAME: ok
 > HOSTNAME exited with 0
G1.I1 - I am the service I1                                       [    OK   ]
start G1.I2 on HOSTNAME
 > /bin/true
start G1.I2 ran in 0.00 s
 > HOSTNAME exited with 0
G1.I2 - I am the service I2                                       [    OK   ]
G1                                                                [    OK   ]
start S3 on HOSTNAME
 > /bin/false
start S3 ran in 0.00 s
 > HOSTNAME exited with 1
S3 - I am the service S3                                          [  ERROR  ]
""",
"""[00:00:00] DEBUG    - Configuration
assumeyes: False
config_dir: 
confirm_actions: []
dryrun: False
excluded_nodes: BADNODE
fanout: 64
nodeps: False
report: no
reverse_actions: ['stop']
summary: False
tags: {setoutput}
verbosity: 5
[I1]\r[I1]\r[I2]\r[I2]\r[S3]\r[S3]\r""".format(setoutput=str(set())))

    def test_multiple_services_reverse(self):
        """CLI reverse execute() with explicit services (S1 S3 -d)"""
        self._output_check(['S1', 'S3', 'stop', '-d', '-x', 'BADNODE'],
                           RC_ERROR,
"""stop S1 will fire in 1 s
stop S1 on HOSTNAME
 > /bin/true
stop S1 ran in 0.00 s
 > HOSTNAME exited with 0
S1 - I am the service S1                                          [    OK   ]
stop S3 on HOSTNAME
 > /bin/false
stop S3 ran in 0.00 s
 > HOSTNAME exited with 1
S3 - I am the service S3                                          [  ERROR  ]
""",
"""[00:00:00] DEBUG    - Configuration
assumeyes: False
config_dir: 
confirm_actions: []
dryrun: False
excluded_nodes: BADNODE
fanout: 64
nodeps: False
report: no
reverse_actions: ['stop']
summary: False
tags: {setoutput}
verbosity: 5
[S1]\r[S1]\r[S1]\r[S3]\r[S3]\r""".format(setoutput=str(set())))

    def test_overall_graph(self):
        """CLI execute() with whole graph (-v -x )"""
        # This could be avoided if the graph is simplified
        self.manager.remove_inter_dep(self.svc2.name)
        self._output_check(['start', '-v', '-x', 'BADNODE'], RC_ERROR,
"""start G1.I1 on HOSTNAME
 > echo ok
G1.I1 - I am the service I1                                       [    OK   ]
start G1.I2 on HOSTNAME
 > /bin/true
G1.I2 - I am the service I2                                       [    OK   ]
G1                                                                [    OK   ]
start S3 on HOSTNAME
 > /bin/false
start S3 ran in 0.00 s
 > HOSTNAME exited with 1
S3 - I am the service S3                                          [  ERROR  ]
S1 - I am the service S1                                          [DEP_ERROR]
""",
"""[I1]\r[I1]\r[I2]\r[I2]\r[S3]\r[S3]\r""")

    def test_overall_graph_reverse(self):
        """CLI reverse execute() with whole graph (-v -x )"""
        # This could be avoided if the graph is simplified
        self.manager.remove_inter_dep(self.svc2.name)
        self._output_check(['stop', '-v', '-x', 'BADNODE'], RC_ERROR,
"""stop S1 on HOSTNAME
 > /bin/true
S1 - I am the service S1                                          [    OK   ]
stop S3 on HOSTNAME
 > /bin/false
stop S3 ran in 0.00 s
 > HOSTNAME exited with 1
S3 - I am the service S3                                          [  ERROR  ]
G1                                                                [DEP_ERROR]
""",
"[S1]\r[S1]\r[S3]\r[S3]\r")

    def test_nodeps_service(self):
        """--nodeps option specifying an explicit service"""
        self._output_check(['S3', 'start', '--nodeps', '-x', 'BADNODE'],
                           RC_ERROR,
"""start S3 ran in 0.00 s
 > HOSTNAME exited with 1
S3 - I am the service S3                                          [  ERROR  ]
""", "[S3]\r")

    def test_nodeps_service_reverse(self):
        """--nodeps option with an explicit service and a reverse action"""
        self._output_check(['S2', 'stop', '--nodeps', '-x', 'BADNODE'], RC_OK,
"""S2 - I am the service S2                                          [    OK   ]
""", "[S2]\r")

    def test_nodeps_all(self):
        """--nodeps option without specifying an explicit service list"""
        self._output_check(['start', '--nodeps', '-x', 'BADNODE'], RC_OK,
"""S1 - I am the service S1                                          [    OK   ]
""", "[S1]\r")

    def test_no_running_status(self):
        """Test if we don't have stderr output when terminal is not a tty"""
        self._output_check(['S2', 'start', '-x', 'BADNODE'], RC_OK,
"""S2 - I am the service S2                                          [    OK   ]
""", "", show_running=False)

class CommandLineOutputTests(CLICommon):
    '''Tests cases of the command line output'''

    def setUp(self):
        '''
        Set up the graph of services within the service manager

        Graph
                              _ start
           group --> service /
                             `- stop
        '''
        CLICommon.setUp(self)

        # ServiceGroup
        group = ServiceGroup('ServiceGroup')
        # Service
        self.service = service = Service('service')
        service.desc = 'I am the service'
        # Actions
        self.start_action = Action('start', command='/bin/true')
        self.stop_action = Action('stop', command='/bin/false')
        self.timeout_action = Action('timeout', command='sleep 1', timeout=0.1)
        self.start_action.inherits_from(service)
        self.stop_action.inherits_from(service)
        service.add_action(self.start_action)
        service.add_action(self.stop_action)
        service.add_action(self.timeout_action)

        # Build graph
        group.add_inter_dep(target=service)

        # Register services within the manager
        self.manager.add_service(group)

    def test_command_output_help(self):
        '''Test command line help output'''
        self._output_check([], RC_OK,
"""Usage: {prog} [options] [SERVICE...] ACTION

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         Increase or decrease verbosity
  -d, --debug           Set debug mode and maximum verbosity
  -g, --graph           Output dependencies graph
  -s, --summary         --summary is an alias for --report=default
  -r REPORT, --report=REPORT
                        Display a report of executed actions
  -c CONFIG_DIR, --config-dir=CONFIG_DIR
                        Change configuration files directory
  -q, --quiet           Enable quiet mode
  -y, --assumeyes       Answer yes to any requested confirmation

  Engine parameters:
    Those options allow you to configure the behaviour of the engine

    -n ONLY_NODES, --only-nodes=ONLY_NODES
                        Use only the specified nodes
    -x EXCLUDED_NODES, --exclude-nodes=EXCLUDED_NODES
                        Exclude the cluster's nodes specified
    -X EXCLUDED_SVC, --exclude-service=EXCLUDED_SVC
                        Skip the specified services
    --dry-run           Only simulate command execution
    -D DEFINES, --define=DEFINES, --var=DEFINES
                        Define custom variables
    --nodeps            Do not run dependencies
    -t TAGS, --tags=TAGS
                        Run services matching these tags
""".format(prog=PROGNAME))

    def test_command_output_checkconfig(self):
        '''Test command line output checking config'''
        self._output_check(['-c', '../conf/samples'], RC_OK,
"""No actions specified, checking configuration...
../conf/samples seems good                     
""" )

    def test_command_line_variables(self):
        '''Test automatic variables from command line.'''
        self._output_check(['ServiceGroup', 'start', '-n', 'fo1', '-x', 'fo2'],
                           RC_OK,
"""ServiceGroup.service - I am the service                           [    OK   ]
ServiceGroup                                                      [    OK   ]
""", "[service]\r")
        self.assertEqual(self.manager.variables['SELECTED_NODES'], 'fo1')
        self.assertEqual(self.manager.variables['EXCLUDED_NODES'], 'fo2')

    def test_command_line_default_variables(self):
        '''Test default values of automatic variables from command line.'''
        self._output_check(['ServiceGroup', 'start'], RC_OK,
"""ServiceGroup.service - I am the service                           [    OK   ]
ServiceGroup                                                      [    OK   ]
""", "[service]\r")
        self.assertEqual(self.manager.variables['SELECTED_NODES'], '')
        self.assertEqual(self.manager.variables['EXCLUDED_NODES'], '')

    def test_command_output_ok(self):
        '''Test command line output with all actions OK'''
        self._output_check(['ServiceGroup', 'start'], RC_OK,
"""ServiceGroup.service - I am the service                           [    OK   ]
ServiceGroup                                                      [    OK   ]
""")

    def test_command_output_ok_verbose2(self):
        '''Test command line output with local action OK in verbose x2'''
        self._output_check(['ServiceGroup', 'start', '-vv'], RC_OK,
"""start ServiceGroup.service on localhost
 > /bin/true
start ServiceGroup.service ran in 0.00 s
 > localhost exited with 0
ServiceGroup.service - I am the service                           [    OK   ]
ServiceGroup                                                      [    OK   ]
""")

    def test_command_output_summary_ok(self):
        '''Test command line output with summary and all actions OK'''
        self._output_check(['ServiceGroup', 'start', '-s'], RC_OK,
"""ServiceGroup.service - I am the service                           [    OK   ]
ServiceGroup                                                      [    OK   ]

 SUMMARY - 1 action (0 failed)
""")

    def test_command_output_full_report_ok(self):
        """Test command line output with full report and all actions OK"""
        self._output_check(['ServiceGroup', 'start', '--report=full'], RC_OK,
"""ServiceGroup.service - I am the service                           [    OK   ]
ServiceGroup                                                      [    OK   ]

 SUMMARY - 1 action (0 failed)
""")

    def test_command_output_error(self):
        '''Test command line output with all actions FAILED'''
        self._output_check(['ServiceGroup', 'stop'], RC_ERROR,
"""stop ServiceGroup.service ran in 0.00 s
 > localhost exited with 1
ServiceGroup.service - I am the service                           [  ERROR  ]
ServiceGroup                                                      [DEP_ERROR]
""")

    def test_command_output_summary_error(self):
        '''Test command line output with summary and all actions FAILED'''
        self._output_check(['ServiceGroup', 'stop', '-s'], RC_ERROR,
"""stop ServiceGroup.service ran in 0.00 s
 > localhost exited with 1
ServiceGroup.service - I am the service                           [  ERROR  ]
ServiceGroup                                                      [DEP_ERROR]

 SUMMARY - 1 action (1 failed)
 + ServiceGroup.service.stop - I am the service
""")

    def test_command_output_dist_summary_error(self):
        """
        Test command line output with summary and all actions FAILED
        on distant nodes.
        """
        self.stop_action._target_backup = "localhost,%s" % HOSTNAME
        nodestring = re.sub(HOSTNAME, 'HOSTNAME', "%s" %
                            NodeSet(self.stop_action._target_backup))
        self._output_check(['ServiceGroup', 'stop', '-s'], RC_ERROR,
"""stop ServiceGroup.service ran in 0.00 s
 > %s exited with 1
ServiceGroup.service - I am the service                           [  ERROR  ]
ServiceGroup                                                      [DEP_ERROR]

 SUMMARY - 1 action (1 failed)
 + ServiceGroup.service.stop - I am the service
""" % nodestring)

    def test_command_output_dist_report_full_error(self):
        """
        Test command line output with full report and all actions FAILED
        on distant nodes.
        """
        self.stop_action._target_backup = "localhost,%s" % HOSTNAME
        nodestring = re.sub(HOSTNAME, 'HOSTNAME', "%s" %
                            NodeSet(self.stop_action._target_backup))
        self._output_check(['ServiceGroup', 'stop', '--report=full'], RC_ERROR,
"""stop ServiceGroup.service ran in 0.00 s
 > %s exited with 1
ServiceGroup.service - I am the service                           [  ERROR  ]
ServiceGroup                                                      [DEP_ERROR]

 SUMMARY - 1 action (1 failed)
 + ServiceGroup.service.stop - I am the service
    Target: %s
    Command: /bin/false
""" % (nodestring, nodestring))

    def test_command_output_dist_report_full_ok(self):
        """
        Test command line output with full report and all actions OK
        on distant nodes.
        """
        self.start_action._target_backup = "localhost,%s" % HOSTNAME
        nodestring = re.sub(HOSTNAME, 'HOSTNAME', "%s" %
                            NodeSet(self.start_action._target_backup))
        self._output_check(['ServiceGroup', 'start', '--report=full'], RC_OK,
"""ServiceGroup.service - I am the service                           [    OK   ]
ServiceGroup                                                      [    OK   ]

 SUMMARY - 1 action (0 failed)
 + Success on all services
    %s
""" % nodestring)

    def test_command_output_dist_report_full_error_and_ok(self):
        """
        Test command line output with full report, FAILED actions and OK
        actions on distant nodes.
        """
        # Service
        svc = Service('service_ok')
        svc.desc = 'I am the ok service'
        svc2 = Service('service_fail')
        svc2.desc = 'I am the fail service'
        svc.add_dep(svc2, sgth=REQUIRE_WEAK)
        # Actions
        false_action = Action('stop', command='/bin/false', target=NodeSet(HOSTNAME))
        false_action.inherits_from(svc)
        svc.add_action(false_action)

        true_action = Action('stop', command='/bin/true', target=NodeSet(HOSTNAME))
        true_action.inherits_from(svc2)
        svc2.add_action(true_action)

        # Register services within the manager
        self.manager.add_service(svc)
        self.manager.add_service(svc2)

        # FIXME: must return RC_OK
        self._output_check(['service_fail', 'stop', '--report=full'], RC_OK,
"""stop service_ok ran in 0.00 s
 > HOSTNAME exited with 1
service_ok - I am the ok service                                  [  ERROR  ]
service_fail - I am the fail service                              [    OK   ]

 SUMMARY - 2 actions (1 failed)
 + service_ok.stop - I am the ok service
    Target: HOSTNAME
    Command: /bin/false
""")

    def test_command_output_timeout(self):
        '''Test command line output with local timeout'''
        self._output_check(['ServiceGroup', 'timeout'], RC_ERROR,
"""timeout ServiceGroup.service ran in 0.00 s
 > localhost has timeout
ServiceGroup.service - I am the service                           [ TIMEOUT ]
ServiceGroup                                                      [DEP_ERROR]
""")

    def test_command_output_dist_timeout(self):
        '''Test command line output with distant timeout'''
        self.timeout_action._target_backup = HOSTNAME
        self._output_check(['ServiceGroup', 'timeout'], RC_ERROR,
"""timeout ServiceGroup.service ran in 0.00 s
 > HOSTNAME has timeout
ServiceGroup.service - I am the service                           [ TIMEOUT ]
ServiceGroup                                                      [DEP_ERROR]
""")

    def test_command_output_multiple_dist_timeout(self):
        '''Test command line output with timeout and multiple distant nodes'''
        self.timeout_action._target_backup = "localhost,%s" % HOSTNAME
        nodestring = re.sub(HOSTNAME, 'HOSTNAME', "%s" %
                            NodeSet(self.timeout_action._target_backup))
        self._output_check(['ServiceGroup', 'timeout'], RC_ERROR,
"""timeout ServiceGroup.service ran in 0.00 s
 > %s has timeout
ServiceGroup.service - I am the service                           [ TIMEOUT ]
ServiceGroup                                                      [DEP_ERROR]
""" % nodestring)

    def test_command_output_summary_multiple_dist_timeout(self):
        """
        Test command line output with timeout, multiple distant nodes
        and summary
        """
        self.timeout_action._target_backup = "localhost,%s" % HOSTNAME
        nodestring = re.sub(HOSTNAME, 'HOSTNAME', "%s" %
                            NodeSet(self.timeout_action._target_backup))
        self._output_check(['ServiceGroup', 'timeout', '-s'], RC_ERROR,
"""timeout ServiceGroup.service ran in 0.00 s
 > %s has timeout
ServiceGroup.service - I am the service                           [ TIMEOUT ]
ServiceGroup                                                      [DEP_ERROR]

 SUMMARY - 1 action (1 failed)
 + ServiceGroup.service.timeout
""" % nodestring)

    def test_command_output_summary_multiple_dist_timeout_full_report(self):
        """
        Test command line output with timeout, multiple distant nodes
        and summary with full report.
        """
        self.timeout_action._target_backup = "localhost,%s" % HOSTNAME
        nodestring = re.sub(HOSTNAME, 'HOSTNAME', "%s" %
                            NodeSet(self.timeout_action._target_backup))
        self._output_check(['ServiceGroup', 'timeout', '--report=full'],
                           RC_ERROR,
"""timeout ServiceGroup.service ran in 0.00 s
 > %s has timeout
ServiceGroup.service - I am the service                           [ TIMEOUT ]
ServiceGroup                                                      [DEP_ERROR]

 SUMMARY - 1 action (1 failed)
 + ServiceGroup.service.timeout
    Target: %s
    Command: sleep 1
""" % (nodestring, nodestring))

    def test_command_output_warning(self):
        '''Test command line output with warning'''
        svc_warn = Service('service_failled')
        svc_warn.desc = 'I am the failled service'
        svc_ok = Service('service_ok')
        svc_ok.desc = 'I am the ok service'
        # Actions
        action = Action('warning', command='/bin/false')
        action.inherits_from(svc_warn)
        svc_warn.add_action(action)
        action = Action('warning', command='/bin/true')
        action.inherits_from(svc_ok)
        svc_ok.add_action(action)

        # Register services within the manager
        svc_ok.add_dep(target=svc_warn, sgth=REQUIRE_WEAK)
        self.manager.add_service(svc_warn)
        self.manager.add_service(svc_ok)

        self._output_check(['service_ok', 'warning'], RC_OK,
"""warning service_failled ran in 0.00 s
 > localhost exited with 1
service_failled - I am the failled service                        [  ERROR  ]
service_ok - I am the ok service                                  [    OK   ]
""")

    def test_command_output_error_quiet(self):
        '''Test command line output with all actions FAILED in quiet mode'''
        self._output_check(['ServiceGroup', 'stop', '-q'], RC_ERROR,
"""ServiceGroup.service - I am the service                           [  ERROR  ]
ServiceGroup                                                      [DEP_ERROR]
""")
    def test_command_output_ok_quiet(self):
        '''Test command line output with all actions OK in quiet mode'''
        self._output_check(['ServiceGroup', 'start', '-q'], RC_OK,
"""ServiceGroup.service - I am the service                           [    OK   ]
ServiceGroup                                                      [    OK   ]
""")

    def test_command_output_warning_status(self):
        '''Test command line output with one action WARNING'''
        svc = Service('warn')
        act = Action('go', command='/bin/false')
        act.errors = 1
        svc.add_action(act)
        self.manager.add_service(svc)
        self._output_check(['warn', 'go', '-q'], RC_WARNING,
"""warn                                                              [ WARNING ]
""")

    def test_custom_defines(self):
        '''Test command line output custom variables'''
        svc = Service('one')
        svc.add_action(Action('go', command='/bin/echo %foo'))
        self.manager.add_service(svc)
        self._output_check(['one', 'go', '-v', '--define=foo=bar'], RC_OK,
"""go one on localhost
 > /bin/echo bar
one                                                               [    OK   ]
""")

    def test_overriding_defines(self):
        """Test command line with overriden variables"""
        tmpdir = tempfile.mkdtemp(prefix='test-mlk-')
        tmpfile = tempfile.NamedTemporaryFile(suffix='.yaml', dir=tmpdir)
        tmpfile.write(textwrap.dedent("""
            variables:
                foo: pub

            services:
              svc:
                actions:
                  start:
                    cmd: echo %foo
                    """).encode())
        tmpfile.flush()

        self._output_check(['svc', 'start', '-v', '-c', tmpdir, '--define', 'foo=bar'], RC_OK,
"""start svc on localhost
 > echo bar
svc                                                               [    OK   ]
""")

class CLIConfigDirTests(CLICommon):

    def setUp(self):
        CLICommon.setUp(self)
        self.manager = ServiceManager()
        ActionManager._instance = None

        # Setup stdout and stderr as a MyOutput file
        sys.stdout = MyOutput()
        sys.stderr = MyOutput()

    def test_config_dir(self):
        """Test --config-dir command line option"""
        try:
            tmpdir = tempfile.mkdtemp(prefix='test-mlk-')
            tmpfile = tempfile.NamedTemporaryFile(suffix='.yaml', dir=tmpdir)
            tmpfile.write(textwrap.dedent("""
                services:
                  svc:
                    actions:
                      start:
                        cmd: echo ok
                        """).encode())
            tmpfile.flush()

            self._output_check(['--config-dir', tmpdir, 'svc', 'start'], RC_OK,
"""svc                                                               [    OK   ]
""")
        finally:
            tmpfile.close()
            os.rmdir(tmpdir)


class MockInterTerminal(MilkCheck.UI.Cli.Terminal):
    '''Manage a fake terminal to test interactive mode'''

    called = False
    user_confirm = True

    @classmethod
    def isinteractive(cls):
        '''Simulate interactive mode'''
        return True

    @classmethod
    def confirm(cls, msg):
        '''Simulate user confirmation'''
        return cls.user_confirm

class MockInteractiveThread(MilkCheck.UI.Cli.InteractiveThread):
    '''Manage a fake thread to test interactive output'''
    display = True
    def _flush_events(self):
        '''Don't flush anything'''
        pass

    def _got_events(self):
        '''Return fake event only once'''
        time.sleep(0.2)
        if self.display :
            self.display = False
            return [(0, select.POLLIN)]

class CommandLineInteractiveOutputTests(CLICommon):
    '''Tests cases of the command line output in interactive mode'''

    def setUp(self):
        '''
        Set up the graph of services within the service manager

        Graph
                                _ start
                   -- service1 /
                 -'             _ start
                  '-- service2 /
        '''

        self.backup_terminal = MilkCheck.UI.Cli.Terminal
        self.backup_interactivethr = MilkCheck.UI.Cli.InteractiveThread
        self.backup_confirm_actions = \
            ConfigParser.DEFAULT_FIELDS['confirm_actions']['value']
        MilkCheck.UI.Cli.Terminal = MockInterTerminal
        MilkCheck.UI.Cli.InteractiveThread = MockInteractiveThread
        MockInterTerminal.called = False
        CLICommon.setUp(self)

        # Service
        service1 = Service('service1')
        service1.desc = 'I am the service 1'
        self.service1 = service1
        service2 = Service('service2')
        service2.desc = 'I am the service 2'
        self.service2 = service2
        # Actions
        action = Action('start', command='/bin/sleep 0.1')
        action.inherits_from(service1)
        service1.add_action(action)

        service2.add_dep(target=service1)

        action = Action('start', command='/bin/sleep 0.8')
        action.inherits_from(service2)
        service2.add_action(action)

        # Register services within the manager
        self.manager.add_service(service1)
        self.manager.add_service(service2)

    def tearDown(self):
        '''Restore MilkCheck.UI.Cli.Terminal'''
        CLICommon.tearDown(self)
        MilkCheck.UI.Cli.Terminal = self.backup_terminal
        MilkCheck.UI.Cli.InteractiveThread = self.backup_interactivethr
        ConfigParser.DEFAULT_FIELDS['confirm_actions']['value'] = \
            self.backup_confirm_actions

    def test_command_output_interactive(self):
        '''Test command line output in interactive mode'''
        self._output_check(['start'], RC_OK,
'''service1 - I am the service 1                                     [    OK   ]

Actions in progress
 > service2.start on localhost

service2 - I am the service 2                                     [    OK   ]
''')

    def test_command_output_interactive_delayed(self):
        '''Test command line output in interactive mode with delayed actions'''
        action = Action('start', command='/bin/sleep 0.1', delay=0.3)
        srv = Service('service')
        srv.desc = 'I am the service'
        action.inherits_from(srv)
        srv.add_action(action)
        self.manager.add_service(srv)
        self._output_check(['service', 'start'], RC_OK,
'''
Actions in progress
 > service.start (delayed for 0.3s) on localhost

service - I am the service                                        [    OK   ]
''')

    def test_interactive_large_nodeset(self):
        '''Test command line output in interactive mode with larget nodeset'''
        class CustomAction(Action):
            def schedule(self, allow_delay=True):
                Action.schedule(self, allow_delay)
                self.pending_target = NodeSet(HOSTNAME + ',foo')

        # Replace start action with a modified one
        act = CustomAction('start', target=HOSTNAME, command='sleep 0.8')
        self.service2.remove_action('start')
        self.service2.add_action(act)

        nodestring = re.sub(HOSTNAME, 'HOSTNAME',
                            str(NodeSet(HOSTNAME + ',foo')))
        self._output_check(['start'], RC_OK,
'''service1 - I am the service 1                                     [    OK   ]

Actions in progress
 > service2.start on %s (2)

service2 - I am the service 2                                     [    OK   ]
''' % nodestring)

    def test_interactive_too_large_nodeset(self):
        '''Test interactive output with too large nodeset is truncated'''
        class CustomAction(Action):
            def schedule(self, allow_delay=True):
                Action.schedule(self, allow_delay)
                longname = "a" * 100
                self.pending_target = NodeSet(HOSTNAME + "," + longname)

        # Replace start action with a modified one
        act = CustomAction('start', target=HOSTNAME, command='sleep 0.8')
        self.service2.remove_action('start')
        self.service2.add_action(act)

        self._output_check(['start'], RC_OK,
'''service1 - I am the service 1                                     [    OK   ]

Actions in progress
 > service2.start on aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa... (2)

service2 - I am the service 2                                     [    OK   ]
''')

    def test_too_large_svc_name(self):
        '''Test output with too large service name is truncated'''
        self.service1.name = "S" * 100
        self.service2.name = "s" * 100
        self._output_check(['start'], RC_OK,
'''SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS...  [    OK   ]

Actions in progress
 > sssssssssssssssssssssssssssssssssssssssssssssssssssss... on localhost

sssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss...  [    OK   ]
''')

    def test_confirm_interactive(self):
        """Test confirm_action with user confirmation"""
        ConfigParser.DEFAULT_FIELDS['confirm_actions']['value'] = ['start']
        # Simulate user confirmation
        MockInterTerminal.user_confirm = True
        self._output_check(['start'], RC_OK,
"""service1 - I am the service 1                                     [    OK   ]

Actions in progress
 > service2.start on localhost

service2 - I am the service 2                                     [    OK   ]
""")

    def test_confirm_assume_yes(self):
        """Test confirm_action with -y"""
        ConfigParser.DEFAULT_FIELDS['confirm_actions']['value'] = ['start']
        # Simulate no user confirmation
        MockInterTerminal.user_confirm = False
        # -y specified => start runs
        self._output_check(['start', '-y'], RC_OK,
"""service1 - I am the service 1                                     [    OK   ]

Actions in progress
 > service2.start on localhost

service2 - I am the service 2                                     [    OK   ]
""")

    def test_confirm_abort(self):
        """Test confirm_action without confirmation"""
        ConfigParser.DEFAULT_FIELDS['confirm_actions']['value'] = ['start']
        # Simulate no user confirmation
        MockInterTerminal.user_confirm = False
        # no -y and user don't confirm: user error
        self._output_check(['start'], RC_EXCEPTION, "",
            "[00:00:00] ERROR    - Execution aborted by user\n")


class CommandLineStderrOutputTests(CLICommon):
    '''Tests cases of the command line output on stderr'''

    def setUp(self):
        '''
        Set up the graph of services within the service manager

        Graph
                                _ start
                   -- service1 /
                 -'             _ start
                  '-- service2 /
        '''
        CLICommon.setUp(self)

        # Service
        self.service1 = Service('service1')
        self.service2 = Service('service2')
        # Actions
        action = Action('start', command='/bin/true')
        action.inherits_from(self.service1)
        self.service1.add_action(action)

        self.service2.add_dep(target=self.service1)

        action = Action('start', command='/bin/true')
        action.inherits_from(self.service2)
        self.service2.add_action(action)

        # Register services within the manager
        self.manager.add_service(self.service1)
        self.manager.add_service(self.service2)

    def test_stderr_too_large_svc_name(self):
        '''Test stderr output with too large service name is truncated'''
        self.service1.name = "S" * 100
        self.service2.name = "s" * 100
        self._output_check(['start'], RC_OK,
                           "%s...  [    OK   ]\n%s...  [    OK   ]\n"
                               % (61 * 'S', 61 * 's'),
                           "[%s...]\r[%s...]\r" % (72 * 'S', 72 * 's'))

    def test_too_large_svc_name_wide_terminal(self):
        '''
        Test output with too large service name is truncated with wide terminal
        '''
        self.service1.name = "S" * 200
        self.service2.name = "s" * 200
        self._output_check(['start'], RC_OK,
                           "%s...  [    OK   ]  \n%s...  [    OK   ]  \n"
                                % (104 * 'S', 104 * 's'),
                           "[%s...]\r[%s...]\r" % (117 * 'S', 117 * 's'),
                           term_width=MAXTERMWIDTH + 2)


def raiser(exception):
    '''Raise exception (used in lambda functions)'''
    raise exception

class CommandLineExceptionsOutputTests(CLICommon):
    '''Tests output messages when an exception occurs'''

    def test_KeyboardInterrupt_output(self):
        '''Test command line output on KeybordInterrupt'''
        self.manager.call_services = \
                lambda services, action, conf=None : raiser(KeyboardInterrupt)
        self._output_check(['start'], (128 + SIGINT),
'''''',
'''[00:00:00] ERROR    - Keyboard Interrupt
''')
    def test_ScannerError_output(self):
        '''Test command line output on ScannerError'''
        self.manager.call_services = \
                lambda services, action, conf=None: raiser(ScannerError)
        self._output_check(['start'], RC_EXCEPTION,
'''''',
'''[00:00:00] ERROR    - 
''')
    def test_ActionNotFound_output(self):
        '''Test command line output on ActionNotFound'''
        self.manager.call_services = \
                lambda services, action, conf=None: raiser(
                                        ActionNotFoundError("Test", "Debug"))
        self._output_check(['start'], RC_EXCEPTION,
'''''',
'''[00:00:00] ERROR    - Action [Debug] not referenced for [Test]
''')
    def test_InvalidOptionError_output(self):
        '''Test command line output on InvalidOption'''
        self.manager.call_services = \
                lambda services, action, conf=None: raiser(InvalidOptionError)
        self._output_check(['start'], RC_EXCEPTION,
'''Usage: {prog} [options] [SERVICE...] ACTION

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         Increase or decrease verbosity
  -d, --debug           Set debug mode and maximum verbosity
  -g, --graph           Output dependencies graph
  -s, --summary         --summary is an alias for --report=default
  -r REPORT, --report=REPORT
                        Display a report of executed actions
  -c CONFIG_DIR, --config-dir=CONFIG_DIR
                        Change configuration files directory
  -q, --quiet           Enable quiet mode
  -y, --assumeyes       Answer yes to any requested confirmation

  Engine parameters:
    Those options allow you to configure the behaviour of the engine

    -n ONLY_NODES, --only-nodes=ONLY_NODES
                        Use only the specified nodes
    -x EXCLUDED_NODES, --exclude-nodes=EXCLUDED_NODES
                        Exclude the cluster's nodes specified
    -X EXCLUDED_SVC, --exclude-service=EXCLUDED_SVC
                        Skip the specified services
    --dry-run           Only simulate command execution
    -D DEFINES, --define=DEFINES, --var=DEFINES
                        Define custom variables
    --nodeps            Do not run dependencies
    -t TAGS, --tags=TAGS
                        Run services matching these tags
'''.format(prog=PROGNAME),
'''[00:00:00] CRITICAL - Invalid options: 

[00:00:00] CRITICAL - Invalid options: 

''')

    def test_ImportException_output(self):
        """Test command line output on ImportError"""
        self.manager.call_services = \
                lambda services, action, conf=None: raiser(ImportError)
        self._output_check(['start'], RC_EXCEPTION, "",
"""[00:00:00] ERROR    - Missing python dependency: 
[00:00:00] ERROR    -   File "source.py", line 000, in raiser
[00:00:00] ERROR    -     raise exception
""")

    def test_UnhandledException_output(self):
        '''Test command line output on UnhandledException'''
        self.manager.call_services = \
                lambda services, action, conf=None: raiser(ZeroDivisionError)
        self._output_check(['start'], RC_UNKNOWN_EXCEPTION,
'''''',
'''[00:00:00] ERROR    - Unexpected Exception : 
''')
    def test_UnhandledExceptionDebug_output(self):
        '''Test command line output on UnhandledException in debug mode'''
        self.manager.call_services = \
                lambda services, action, conf=None: raiser(ZeroDivisionError)
        # remove decoration from traceback
        import traceback
        traceback._Anchors=[]
        # python2 didn't have line decoration (~~~~~^^^^)
        self._output_check(['start', '-d'], RC_UNKNOWN_EXCEPTION,
'''Traceback (most recent call last):
  File "source.py", line 000, in execute
    self.manager.call_services(services, action, conf=self._conf)
  File "source.py", line 000, in <lambda>
    lambda services, action, conf=None: raiser(ZeroDivisionError)
  File "source.py", line 000, in raiser
    raise exception
ZeroDivisionError
''',
'''[00:00:00] DEBUG    - Configuration
assumeyes: False
config_dir: 
confirm_actions: []
dryrun: False
fanout: 64
nodeps: False
report: no
reverse_actions: ['stop']
summary: False
tags: {setoutput}
verbosity: 5
'''.format(setoutput=str(set())))

class ConsoleOutputTest(TestCase):
    '''Tests console output'''

    def setUp(self):
        '''
        Set up display
        '''
        self.display = ConsoleDisplay()

    def tearDown(self):
        '''Restore'''
        pass

    def test_len_color(self):
        '''Test len computation with color'''
        self.display._color = True
        test_str = "Test"
        test_str_colored = self.display.string_color(test_str, 'GREEN')
        self.assertEqual(len(test_str_colored) - self.display.escape,
                         len(test_str))
        self.assertNotEqual(len(test_str_colored), len(test_str),
                            "String must be longer when colored")

    def test_len_without_color(self):
        '''Test len computation without color'''
        self.display._color = False
        test_str = "Test"
        test_str_colored = self.display.string_color(test_str, 'GREEN')
        self.assertEqual(len(test_str_colored), len(test_str))
