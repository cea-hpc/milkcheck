# Copyright CEA (2011)
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This modules defines the tests cases targeting the class CommandLineInterface
"""

# Classes
import socket, sys, re
from StringIO import StringIO

from unittest import TestCase

from MilkCheck.UI.Cli import CommandLineInterface
from MilkCheck.ServiceManager import ServiceManager
from MilkCheck.ServiceManager import service_manager_self
from MilkCheck.Engine.Service import Service
from MilkCheck.Engine.Action import Action
from MilkCheck.Engine.ServiceGroup import ServiceGroup
from MilkCheck.Callback import CallbackHandler
from MilkCheck.Config.ConfigParser import ConfigParser
from ClusterShell.NodeSet import NodeSet

# Symbols
from MilkCheck.UI.Cli import RC_OK, RC_ERROR, RC_EXCEPTION, RC_WARNING, \
                             RC_UNKNOWN_EXCEPTION
from MilkCheck.Engine.BaseEntity import REQUIRE_WEAK

HOSTNAME = socket.gethostname().split('.')[0]

class MyOutput(StringIO):
    ''' Class replacing stdout to manage output in nosetest '''

    def write(self, line):
        ''' Writes a word per line'''

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

        StringIO.write(self, line)


class CLICommon(TestCase):

    def setUp(self):
        ConfigParser.DEFAULT_FIELDS['config_dir']['value'] = ''
        ConfigParser.CONFIG_PATH = '/dev/null'

        ServiceManager._instance = None 
        self.manager = service_manager_self()

        # Setup stdout and stderr as a MyOutput file
        sys.stdout = MyOutput()
        sys.stderr = MyOutput()

    def tearDown(self):
        '''Restore sys.stdout and sys.stderr'''
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        CallbackHandler._instance = None

    def _output_check(self, args, retcode, outexpected, errexpected=None):
        """
        Test Milcheck output with:
         - args: command line args for cli.execute
         - outexpected: expected std output
         - errexpected: optional expected stderr
        """
        cli = CommandLineInterface()
        cli._console.cleanup = False
        cli._console._term_width = 77
        rc = cli.execute(args)

        # STDOUT
        msg = sys.stdout.getvalue()
        for line1, line2 in zip(outexpected.splitlines(), msg.splitlines()):
            self.assertEqual(line1, line2)
        self.assertEqual(outexpected, msg)

        # STDERR
        if errexpected:
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
"""I1 - I am the service I1                                          [    OK   ]
start I2 ran in 0.00 s
 > BADNODE: ssh: Could not resolve hostname BADNODE: Name or service not known
 > HOSTNAME exited with 0
 > BADNODE exited with 255
I2 - I am the service I2                                          [  ERROR  ]
G1                                                                [DEP_ERROR]
S3 - I am the service S3                                          [DEP_ERROR]
""")

    def test_execute_verbosity_1(self):
        '''CLI execute() (-v)'''
        self._output_check(['S3', 'start', '-v'], RC_ERROR,
"""start I1 on HOSTNAME
 > echo ok
I1 - I am the service I1                                          [    OK   ]
start I2 on BADNODE,HOSTNAME
 > /bin/true
start I2 ran in 0.00 s
 > BADNODE: ssh: Could not resolve hostname BADNODE: Name or service not known
 > HOSTNAME exited with 0
 > BADNODE exited with 255
I2 - I am the service I2                                          [  ERROR  ]
G1                                                                [DEP_ERROR]
S3 - I am the service S3                                          [DEP_ERROR]
""")

    def test_execute_verbosity_2(self):
        '''CLI execute() (-vv)'''
        self._output_check(['S3', 'start', '-vv'], RC_ERROR,
"""start I1 on HOSTNAME
 > echo ok
start I1 ran in 0.00 s
 > HOSTNAME: ok
 > HOSTNAME exited with 0
I1 - I am the service I1                                          [    OK   ]
start I2 on BADNODE,HOSTNAME
 > /bin/true
start I2 ran in 0.00 s
 > BADNODE: ssh: Could not resolve hostname BADNODE: Name or service not known
 > HOSTNAME exited with 0
 > BADNODE exited with 255
I2 - I am the service I2                                          [  ERROR  ]
G1                                                                [DEP_ERROR]
S3 - I am the service S3                                          [DEP_ERROR]
""")

    def test_execute_debug(self):
        '''CLI execute() (-d)'''
        self._output_check(['S3', 'start', '-d'], RC_ERROR,
"""start I1 on HOSTNAME
 > echo ok
start I1 ran in 0.00 s
 > HOSTNAME: ok
 > HOSTNAME exited with 0
I1 - I am the service I1                                          [    OK   ]
start I2 on BADNODE,HOSTNAME
 > /bin/true
start I2 ran in 0.00 s
 > BADNODE: ssh: Could not resolve hostname BADNODE: Name or service not known
 > HOSTNAME exited with 0
 > BADNODE exited with 255
I2 - I am the service I2                                          [  ERROR  ]
G1                                                                [DEP_ERROR]
S3 - I am the service S3                                          [DEP_ERROR]
""",
"""[00:00:00] DEBUG    - Configuration
dryrun: False
verbosity: 5
summary: False
fanout: 64
debug: True
config_dir: 
\r\r[I1]\r\r\r[I1]\r\r\r[I2]\r\r\r[I2]\r""")

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
"""start I1 on HOSTNAME
 > echo ok
start I1 ran in 0.00 s
 > HOSTNAME: ok
 > HOSTNAME exited with 0
I1 - I am the service I1                                          [    OK   ]
start I2 on HOSTNAME
 > /bin/true
start I2 ran in 0.00 s
 > HOSTNAME exited with 0
I2 - I am the service I2                                          [    OK   ]
G1                                                                [    OK   ]
start S3 on HOSTNAME
 > /bin/false
start S3 ran in 0.00 s
 > HOSTNAME exited with 1
S3 - I am the service S3                                          [  ERROR  ]
""",
"""[00:00:00] DEBUG    - Configuration
dryrun: False
verbosity: 5
only_nodes: HOSTNAME
summary: False
fanout: 64
debug: True
config_dir: 
\r\r[I1]\r\r\r[I1]\r\r\r[I2]\r\r\r[I2]\r\r\r[S3]\r\r\r[S3]\r""")

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
"""[00:00:00] ERROR    - Unexpected Exception : 'NoneType' object is not callable
""")

    def test_multiple_services(self):
        """CLI execute() with explicit services (S1 G1 -d)"""
        self._output_check(['S3', 'G1', 'start', '-d', '-x', 'BADNODE'],
                           RC_ERROR,
"""start I1 on HOSTNAME
 > echo ok
start I1 ran in 0.00 s
 > HOSTNAME: ok
 > HOSTNAME exited with 0
I1 - I am the service I1                                          [    OK   ]
start I2 on HOSTNAME
 > /bin/true
start I2 ran in 0.00 s
 > HOSTNAME exited with 0
I2 - I am the service I2                                          [    OK   ]
G1                                                                [    OK   ]
start S3 on HOSTNAME
 > /bin/false
start S3 ran in 0.00 s
 > HOSTNAME exited with 1
S3 - I am the service S3                                          [  ERROR  ]
""",
"""[00:00:00] DEBUG    - Configuration
dryrun: False
verbosity: 5
summary: False
excluded_nodes: BADNODE
fanout: 64
debug: True
config_dir: 
\r\r[I1]\r\r\r[I1]\r\r\r[I2]\r\r\r[I2]\r\r\r[S3]\r\r\r[S3]\r""")

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
dryrun: False
verbosity: 5
summary: False
excluded_nodes: BADNODE
fanout: 64
debug: True
config_dir: 
\r\r[S1]\r\r\r[S1]\r\r\r[S1]\r\r\r[S3]\r\r\r[S3]\r""")

    def test_overall_graph(self):
        """CLI execute() with whole graph (-v -x )"""
        # This could be avoided if the graph is simplified
        self.manager.forget_services(self.svc2)
        self._output_check(['start', '-v', '-x', 'BADNODE'], RC_ERROR,
"""start I1 on HOSTNAME
 > echo ok
I1 - I am the service I1                                          [    OK   ]
start I2 on HOSTNAME
 > /bin/true
I2 - I am the service I2                                          [    OK   ]
G1                                                                [    OK   ]
start S3 on HOSTNAME
 > /bin/false
start S3 ran in 0.00 s
 > HOSTNAME exited with 1
S3 - I am the service S3                                          [  ERROR  ]
S1 - I am the service S1                                          [DEP_ERROR]
""",
"""\r\r[I1]\r\r\r[I1]\r\r\r[I2]\r\r\r[I2]\r\r\r[S3]\r\r\r[S3]\r""")

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
"")

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
        start_action.inherits_from(service)
        stop_action.inherits_from(service)
        service.add_action(start_action)
        service.add_action(stop_action)

        # Build graph
        group.add_inter_dep(target=service)
        service.parent = group

        # Register services within the manager
        self.manager.register_services(group, service)

    def test_command_output_help(self):
        '''Test command line help output'''
        if sys.version_info[0] == 2 and sys.version_info[1] < 5:
            self._output_check([], RC_OK,
"""usage: nosetests [options] [SERVICE...] ACTION

options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         Increase or decrease verbosity
  -d, --debug           Set debug mode and maximum verbosity
  -g, --graph           Output dependencies graph
  -s, --summary         Display summary of executed actions
  -c CONFIG_DIR, --config-dir=CONFIG_DIR
                        Change configuration files directory

  Engine parameters:
    Those options allow you to configure the behaviour of the engine

    -n ONLY_NODES, --only-nodes=ONLY_NODES
                        Use only the specified nodes
    -x EXCLUDED_NODES, --exclude-nodes=EXCLUDED_NODES
                        Exclude the cluster's nodes specified
    -X EXCLUDED_SVC, --exclude-service=EXCLUDED_SVC
                        Skip the specified services
    --dry-run           Only simulate command execution
""")
        else:
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

  Engine parameters:
    Those options allow you to configure the behaviour of the engine

    -n ONLY_NODES, --only-nodes=ONLY_NODES
                        Use only the specified nodes
    -x EXCLUDED_NODES, --exclude-nodes=EXCLUDED_NODES
                        Exclude the cluster's nodes specified
    -X EXCLUDED_SVC, --exclude-service=EXCLUDED_SVC
                        Skip the specified services
    --dry-run           Only simulate command execution
""")

    def test_command_output_checkconfig(self):
        '''Test command line output checking config'''
        self._output_check(['-c', '../conf/base'], RC_OK,
"""No actions specified, checking configuration...
../conf/base seems good
""" )

    def test_command_line_variables(self):
        '''Test automatic variables from command line.'''
        self._output_check(['ServiceGroup', 'start', '-n', 'fo1', '-x', 'fo2'],
                           RC_OK,
"""ServiceGroup.service - I am the service                           [    OK   ]
ServiceGroup                                                      [    OK   ]
""", "")
        self.assertEqual(self.manager.variables['SELECTED_NODES'], 'fo1')
        self.assertEqual(self.manager.variables['EXCLUDED_NODES'], 'fo2')

    def test_command_line_default_variables(self):
        '''Test default values of automatic variables from command line.'''
        self._output_check(['ServiceGroup', 'start'], RC_OK,
"""ServiceGroup.service - I am the service                           [    OK   ]
ServiceGroup                                                      [    OK   ]
""", "")
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
        self.service.add_action(Action('timeout', command='/bin/sleep 1',
                                       timeout=0.1))
        self._output_check(['ServiceGroup', 'timeout'], RC_ERROR,
"""timeout ServiceGroup.service ran in 0.00 s
 > localhost has timeout
ServiceGroup.service - I am the service                           [ TIMEOUT ]
ServiceGroup                                                      [DEP_ERROR]
""")

    def test_command_output_dist_timeout(self):
        '''Test command line output with distant timeout'''
        self.service.add_action(Action('dist_timeout', HOSTNAME,
                                       command='/bin/sleep 1', timeout=0.1))
        self._output_check(['ServiceGroup', 'dist_timeout'], RC_ERROR,
"""dist_timeout ServiceGroup.service ran in 0.00 s
 > HOSTNAME has timeout
ServiceGroup.service - I am the service                           [ TIMEOUT ]
ServiceGroup                                                      [DEP_ERROR]
""")

    def test_command_output_multiple_dist_timeout(self):
        '''Test command line output with timeout and multiple distant nodes'''
        self.service.add_action(Action('multiple_dist_timeout',
                                       NodeSet("localhost,%s" % HOSTNAME),
                                       command='/bin/sleep 1', timeout=0.1))
        self._output_check(['ServiceGroup', 'multiple_dist_timeout'], RC_ERROR,
"""multiple_dist_timeout ServiceGroup.service ran in 0.00 s
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

        self._output_check(['service_ok', 'warning'], RC_WARNING,
"""warning service_failled ran in 0.00 s
 > localhost exited with 1
service_failled - I am the failled service                        [  ERROR  ]
service_ok - I am the ok service                                  [ WARNING ]
""")
