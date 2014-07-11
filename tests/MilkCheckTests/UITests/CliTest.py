# Copyright CEA (2011)
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This modules defines the tests cases targeting the class CommandLine
"""

# Classes
import socket, sys, re, time, select
from StringIO import StringIO

from unittest import TestCase

import MilkCheck.UI.Cli
from MilkCheck.UI.Cli import CommandLine, ConsoleDisplay, MAXTERMWIDTH
import MilkCheck.ServiceManager
from MilkCheck.ServiceManager import ServiceManager, service_manager_self
from MilkCheck.Engine.Service import Service
from MilkCheck.Engine.Action import Action, ActionManager
from MilkCheck.Engine.ServiceGroup import ServiceGroup
from MilkCheck.Callback import CallbackHandler
from MilkCheck.Config.ConfigParser import ConfigParser
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

HOSTNAME = socket.gethostname().split('.')[0]

class MyOutput(StringIO):
    ''' Class replacing stdout to manage output in nosetest '''

    def write(self, line):
        ''' Writes a word per line'''

        # Format help usage
        line = re.sub('^usage: ', 'Usage: ', line)
        line = re.sub('\noptions:\n', '\nOptions:\n', line)

        # Clear secounds elapsed
        line = re.sub(' [0-9]+\.[0-9]+ s', ' 0.00 s', line)
        # All time related to midnight
        line = re.sub('\[[0-9]{2}:[0-9]{2}:[0-9]{2}\] ', '[00:00:00] ', line)
        # Replace local hostname by "HOSTNAME"
        line = re.sub(HOSTNAME, 'HOSTNAME', line)

        # SSH output is different with OpenSSH (4.x ?)
        # We modify the output to match those from OpenSSH 5.x
        line = re.sub('ssh: (\w+): (Name or service not known)',
                      'ssh: Could not resolve hostname \\1: \\2', line)

        # Traceback output doesn't need line number and source location
        line = re.sub('File .*, line .*, in (.*)',
                      'File "source.py", line 000, in \\1', line)
        StringIO.write(self, line)

class CLICommon(TestCase):
    ''' Class to manage Cli in tests'''

    def setUp(self):
        ConfigParser.DEFAULT_FIELDS['config_dir']['value'] = ''
        ConfigParser.CONFIG_PATH = '/dev/null'

        ServiceManager._instance = None 
        self.manager = service_manager_self()
        ActionManager._instance = None

        # Setup stdout and stderr as a MyOutput file
        sys.stdout = MyOutput()
        sys.stderr = MyOutput()

    def tearDown(self):
        '''Restore sys.stdout and sys.stderr'''
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        CallbackHandler._instance = None

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
        cli._console.cleanup = False
        cli._console._term_width = term_width
        cli._console._show_running = show_running
        rc = cli.execute(args)

        # STDOUT
        msg = sys.stdout.getvalue()
        for line1, line2 in zip(outexpected.splitlines(), msg.splitlines()):
            self.assertEqual(line1, line2)
        self.assertEqual(outexpected, msg)

        # STDERR
        if errexpected is not None:
            msg = sys.stderr.getvalue()
            for line1, line2 in zip(errexpected.splitlines(), msg.splitlines()):
                self.assertEqual(line1, line2)
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
        self.manager.register_services(svc1, svc2, svc3, group1)

    def test_execute_std_verbosity(self):
        '''CLI execute() (no option)'''
        self._output_check(['S3', 'start'], RC_ERROR,
"""G1.I1 - I am the service I1                                       [    OK   ]
start G1.I2 ran in 0.00 s
 > BADNODE: ssh: Could not resolve hostname BADNODE: Name or service not known
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
start G1.I2 on BADNODE,HOSTNAME
 > /bin/true
start G1.I2 ran in 0.00 s
 > BADNODE: ssh: Could not resolve hostname BADNODE: Name or service not known
 > HOSTNAME exited with 0
 > BADNODE exited with 255
G1.I2 - I am the service I2                                       [  ERROR  ]
G1                                                                [DEP_ERROR]
S3 - I am the service S3                                          [DEP_ERROR]
""")

    def test_execute_verbosity_2(self):
        '''CLI execute() (-vv)'''
        self._output_check(['S3', 'start', '-vv'], RC_ERROR,
"""start G1.I1 on HOSTNAME
 > echo ok
start G1.I1 ran in 0.00 s
 > HOSTNAME: ok
 > HOSTNAME exited with 0
G1.I1 - I am the service I1                                       [    OK   ]
start G1.I2 on BADNODE,HOSTNAME
 > /bin/true
start G1.I2 ran in 0.00 s
 > BADNODE: ssh: Could not resolve hostname BADNODE: Name or service not known
 > HOSTNAME exited with 0
 > BADNODE exited with 255
G1.I2 - I am the service I2                                       [  ERROR  ]
G1                                                                [DEP_ERROR]
S3 - I am the service S3                                          [DEP_ERROR]
""")

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
 > BADNODE: ssh: Could not resolve hostname BADNODE: Name or service not known
 > HOSTNAME exited with 0
 > BADNODE exited with 255
G1.I2 - I am the service I2                                       [  ERROR  ]
G1                                                                [DEP_ERROR]
S3 - I am the service S3                                          [DEP_ERROR]
""",
"""[00:00:00] DEBUG    - Configuration
nodeps: False
dryrun: False
verbosity: 5
summary: False
fanout: 64
reverse_actions: ['stop']
debug: True
config_dir: 
[I1]\r[I1]\r[I2]\r[I2]\r""")

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
nodeps: False
dryrun: False
verbosity: 5
only_nodes: HOSTNAME
summary: False
fanout: 64
reverse_actions: ['stop']
debug: True
config_dir: 
[I1]\r[I1]\r[I2]\r[I2]\r[S3]\r[S3]\r""")

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
        service_manager_self().call_services = None
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
nodeps: False
dryrun: False
verbosity: 5
summary: False
excluded_nodes: BADNODE
fanout: 64
reverse_actions: ['stop']
debug: True
config_dir: 
[I1]\r[I1]\r[I2]\r[I2]\r[S3]\r[S3]\r""")

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
nodeps: False
dryrun: False
verbosity: 5
summary: False
excluded_nodes: BADNODE
fanout: 64
reverse_actions: ['stop']
debug: True
config_dir: 
[S1]\r[S1]\r[S1]\r[S3]\r[S3]\r""")

    def test_overall_graph(self):
        """CLI execute() with whole graph (-v -x )"""
        # This could be avoided if the graph is simplified
        self.manager.forget_services(self.svc2)
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
        self.manager.forget_services(self.svc2)
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
        start_action = Action('start', command='/bin/true')
        stop_action = Action('stop', command='/bin/false')
        self.timeout_action = Action('timeout', command='sleep 1', timeout=0.1)
        start_action.inherits_from(service)
        stop_action.inherits_from(service)
        service.add_action(start_action)
        service.add_action(stop_action)
        service.add_action(self.timeout_action)

        # Build graph
        group.add_inter_dep(target=service)

        # Register services within the manager
        self.manager.register_services(group, service)

    def test_command_output_help(self):
        '''Test command line help output'''
        self._output_check([], RC_OK,
"""Usage: nosetests [options] [SERVICE...] ACTION

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         Increase or decrease verbosity
  -d, --debug           Set debug mode and maximum verbosity
  -g, --graph           Output dependencies graph
  -s, --summary         Display summary of executed actions
  -c CONFIG_DIR, --config-dir=CONFIG_DIR
                        Change configuration files directory
  -q, --quiet           Enable quiet mode

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
""")

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
        self._output_check(['ServiceGroup', 'timeout'], RC_ERROR,
"""timeout ServiceGroup.service ran in 0.00 s
 > HOSTNAME,localhost has timeout
ServiceGroup.service - I am the service                           [ TIMEOUT ]
ServiceGroup                                                      [DEP_ERROR]
""")

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
        self.manager.register_services(svc_warn, svc_ok)

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
        self.manager.register_service(svc)
        self._output_check(['warn', 'go', '-q'], RC_WARNING,
"""warn                                                              [ WARNING ]
""")
    def test_custom_defines(self):
        '''Test command line output custom variables'''
        svc = Service('one')
        svc.add_action(Action('go', command='/bin/echo %foo'))
        self.manager.register_service(svc)
        self._output_check(['one', 'go', '-v', '--define=foo=bar'], RC_OK,
"""go one on localhost
 > /bin/echo bar
one                                                               [    OK   ]
""")


class MockInterTerminal(MilkCheck.UI.Cli.Terminal):
    '''Manage a fake terminal to test interactive mode'''

    called = False

    @classmethod
    def isinteractive(cls):
        '''Simulate interactive mode'''
        return True

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
        MilkCheck.UI.Cli.Terminal = MockInterTerminal
        MilkCheck.UI.Cli.InteractiveThread = MockInteractiveThread
        MockInterTerminal.called = False
        CLICommon.setUp(self)

        # Service
        service1 = Service('service1')
        service1.desc = 'I am the service 1'
        service2 = Service('service2')
        service2.desc = 'I am the service 2'
        # Actions
        action = Action('start', command='/bin/sleep 0.1')
        action.inherits_from(service1)
        service1.add_action(action)

        service2.add_dep(target=service1)

        action = Action('start', command='/bin/sleep 0.8')
        action.inherits_from(service2)
        service2.add_action(action)

        # Register services within the manager
        self.manager.register_services(service1, service2)

    def tearDown(self):
        '''Restore MilkCheck.UI.Cli.Terminal'''
        CLICommon.tearDown(self)
        MilkCheck.UI.Cli.Terminal = self.backup_terminal
        MilkCheck.UI.Cli.InteractiveThread = self.backup_interactivethr

    def test_command_output_interactive(self):
        '''Test command line output in interactive mode'''
        self._output_check(['start'], RC_OK,
'''service1 - I am the service 1                                     [    OK   ]

Actions in progress
 > service2.start on localhost

service2 - I am the service 2                                     [    OK   ]
''')

    def test_interactive_large_nodeset(self):
        '''Test command line output in interactive mode with larget nodeset'''
        class CustomAction(Action):
            def schedule(self, allow_delay=True):
                Action.schedule(self, allow_delay)
                self.pending_target = NodeSet(HOSTNAME + ',foo')

        # Replace start action with a modified one
        act = CustomAction('start', target=HOSTNAME, command='sleep 0.8')
        svc2 = self.manager.entities['service2']
        svc2.remove_action('start')
        svc2.add_action(act)

        self._output_check(['start'], RC_OK,
'''service1 - I am the service 1                                     [    OK   ]

Actions in progress
 > service2.start on HOSTNAME,foo (2)

service2 - I am the service 2                                     [    OK   ]
''')

    def test_interactive_too_large_nodeset(self):
        '''Test interactive output with too large nodeset is truncated'''
        class CustomAction(Action):
            def schedule(self, allow_delay=True):
                Action.schedule(self, allow_delay)
                longname = "a" * 100
                self.pending_target = NodeSet(HOSTNAME + "," + longname)

        # Replace start action with a modified one
        act = CustomAction('start', target=HOSTNAME, command='sleep 0.8')
        svc2 = self.manager.entities['service2']
        svc2.remove_action('start')
        svc2.add_action(act)

        self._output_check(['start'], RC_OK,
'''service1 - I am the service 1                                     [    OK   ]

Actions in progress
 > service2.start on aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa... (2)

service2 - I am the service 2                                     [    OK   ]
''')

    def test_too_large_svc_name(self):
        '''Test output with too large service name is truncated'''
        # Add a new service
        self.manager.entities['service1'].name = "S" * 100
        self.manager.entities['service2'].name = "s" * 100
        self._output_check(['start'], RC_OK,
'''SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS...  [    OK   ]

Actions in progress
 > sssssssssssssssssssssssssssssssssssssssssssssssssssss... on localhost

sssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss...  [    OK   ]
''')

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
        service1 = Service('service1')
        service1.desc = 'I am the service 1'
        service2 = Service('service2')
        service2.desc = 'I am the service 2'
        # Actions
        action = Action('start', command='/bin/true')
        action.inherits_from(service1)
        service1.add_action(action)

        service2.add_dep(target=service1)

        action = Action('start', command='/bin/true')
        action.inherits_from(service2)
        service2.add_action(action)

        # Register services within the manager
        self.manager.register_services(service1, service2)

    def tearDown(self):
        '''Restore MilkCheck.UI.Cli.Terminal'''
        CLICommon.tearDown(self)

    def test_stderr_too_large_svc_name(self):
        '''Test stderr output with too large service name is truncated'''
        # Add a new service
        self.manager.entities['service1'].name = "S" * 100
        self.manager.entities['service2'].name = "s" * 100
        self._output_check(['start'], RC_OK,
'''%s...  [    OK   ]\n%s...  [    OK   ]\n''' % ((61 * 'S'), (61 * 's')),
'''[%s...]\r[%s...]\r''' % ((72 * 'S'), (72 * 's')))

    def test_too_large_svc_name_wide_terminal(self):
        '''
        Test output with too large service name is truncated with wide terminal
        '''
        # Add a new service
        self.manager.entities['service1'].name = "S" * 200
        self.manager.entities['service2'].name = "s" * 200
        self._output_check(['start'], RC_OK,
'''%s...  [    OK   ]  \n%s...  [    OK   ]  
''' % ((104 * 'S'), (104 * 's')),
'''[%s...]\r[%s...]\r''' % ((117 * 'S'), (117 * 's')),
term_width=MAXTERMWIDTH + 2)

def raiser(exception):
    '''Raise exception (used in lambda functions)'''
    raise exception

class CommandLineExceptionsOutputTests(CLICommon):
    '''Tests output messages when an exception occurs'''

    def setUp(self):
        '''
        Set up mocking to test exceptions
        '''
        CLICommon.setUp(self)
        self.call_services_backup = service_manager_self().call_services

    def tearDown(self):
        '''Restore ServiceManager'''
        CLICommon.tearDown(self)
        service_manager_self().call_services = self.call_services_backup

    def test_KeyboardInterrupt_output(self):
        '''Test command line output on KeybordInterrupt'''
        service_manager_self().call_services = \
                lambda services, action, conf=None : raiser(KeyboardInterrupt)
        self._output_check(['start'], (128 + SIGINT),
'''''',
'''[00:00:00] ERROR    - Keyboard Interrupt
''')
    def test_ScannerError_output(self):
        '''Test command line output on ScannerError'''
        service_manager_self().call_services = \
                lambda services, action, conf=None: raiser(ScannerError)
        self._output_check(['start'], RC_EXCEPTION,
'''''',
'''[00:00:00] ERROR    - 
''')
    def test_ActionNotFound_output(self):
        '''Test command line output on ActionNotFound'''
        service_manager_self().call_services = \
                lambda services, action, conf=None: raiser(
                                        ActionNotFoundError("Test", "Debug"))
        self._output_check(['start'], RC_EXCEPTION,
'''''',
'''[00:00:00] ERROR    - Action [Debug] not referenced for [Test]
''')
    def test_InvalidOptionError_output(self):
        '''Test command line output on InvalidOption'''
        service_manager_self().call_services = \
                lambda services, action, conf=None: raiser(InvalidOptionError)
        self._output_check(['start'], RC_EXCEPTION,
'''Usage: nosetests [options] [SERVICE...] ACTION

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         Increase or decrease verbosity
  -d, --debug           Set debug mode and maximum verbosity
  -g, --graph           Output dependencies graph
  -s, --summary         Display summary of executed actions
  -c CONFIG_DIR, --config-dir=CONFIG_DIR
                        Change configuration files directory
  -q, --quiet           Enable quiet mode

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
''',
'''[00:00:00] CRITICAL - Invalid options: 

[00:00:00] CRITICAL - Invalid options: 

''')
    def test_UnhandledException_output(self):
        '''Test command line output on UnhandledException'''
        service_manager_self().call_services = \
                lambda services, action, conf=None: raiser(ZeroDivisionError)
        self._output_check(['start'], RC_UNKNOWN_EXCEPTION,
'''''',
'''[00:00:00] ERROR    - Unexpected Exception : 
''')
    def test_UnhandledExceptionDebug_output(self):
        '''Test command line output on UnhandledException in debug mode'''
        service_manager_self().call_services = \
                lambda services, action, conf=None: raiser(ZeroDivisionError)
        self._output_check(['start', '-d'], RC_UNKNOWN_EXCEPTION,
'''Traceback (most recent call last):
  File "source.py", line 000, in execute
    manager.call_services(services, action, conf=self._conf)
  File "source.py", line 000, in <lambda>
    lambda services, action, conf=None: raiser(ZeroDivisionError)
  File "source.py", line 000, in raiser
    raise exception
ZeroDivisionError
''',
'''[00:00:00] DEBUG    - Configuration
nodeps: False
dryrun: False
verbosity: 5
summary: False
fanout: 64
reverse_actions: ['stop']
debug: True
config_dir: 
''')

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
