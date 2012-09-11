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
from MilkCheck.Engine.BaseEntity import DONE, ERROR, DEP_ERROR
from MilkCheck.UI.UserView import RC_OK, RC_ERROR, RC_EXCEPTION

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

class CommandLineInterfaceTests(TestCase):
    '''Tests cases of the command line interface'''

    def setUp(self):
        '''
        Set up the graph of services within the service manager

        Graph
                ---> S2
            S1                            --> I1 
                        ---> G1 --> (sour)       --> (sink)
                ---> S3                   --> I2 
                        ---> S4

        Each node has an action start and an action stop
        '''

        ConfigParser.DEFAULT_FIELDS['config_dir']['value'] = ''
        ConfigParser.CONFIG_PATH = '/dev/null'

        ServiceManager._instance = None 
        manager = service_manager_self()
        s1 = Service('S1')
        s1.desc = 'I am the service S1'
        s2 = Service('S2')
        s2.desc = 'I am the service S2'
        s3 = Service('S3')
        s3.desc = 'I am the service S3'
        s4 = Service('S4')
        s4.desc = 'I am the service S4'
        g1 = ServiceGroup('G1')
        i1 = Service('I1')
        i1.desc = 'I am the service I1'
        i2 = Service('I2')
        i2.desc = 'I am the service I2'

        # Actions S1
        start_s1 = Action('start', HOSTNAME + ', fortoy8', '/bin/true')
        start_s1.delay = 1
        stop_s1 = Action('stop', HOSTNAME + ',fortoy8', '/bin/true')
        stop_s1.delay = 1
        s1.add_actions(start_s1, stop_s1)
        # Actions S2
        start_s2 = Action('start', HOSTNAME + ',fortoy8', '/bin/true')
        stop_s2 = Action('stop', HOSTNAME + ',fortoy8', '/bin/true')
        s2.add_actions(start_s2, stop_s2)
        # Actions S3
        start_s3 = Action('start', HOSTNAME + ',fortoy8', '/bin/false')
        stop_s3 = Action('stop', HOSTNAME + ',fortoy8', '/bin/false')
        s3.add_actions(start_s3, stop_s3)
        # Actions S4
        start_s4 = Action('start', HOSTNAME + ',fortoy8', 'hostname')
        stop_s4 = Action('stop', HOSTNAME + ',fortoy8', '/bin/true')
        s4.add_actions(start_s4, stop_s4)
        # Actions I1
        start_i1 = Action('start', HOSTNAME + ',fortoy8', '/bin/true')
        stop_i1 = Action('stop', HOSTNAME + ',fortoy8', '/bin/true')
        i1.add_actions(start_i1, stop_i1)
        # Actions I2
        start_i2 = Action('start', HOSTNAME + ',fortoy8', '/bin/true')
        stop_i2 = Action('stop', HOSTNAME + ',fortoy8', '/bin/true')
        i2.add_actions(start_i2, stop_i2)

        # Build graph
        s1.add_dep(target=s2)
        s1.add_dep(target=s3)
        s3.add_dep(target=g1)
        s3.add_dep(target=s4)
        g1.add_inter_dep(target=i1)
        g1.add_inter_dep(target=i2)

        # Register services within the manager
        manager.register_services(s1, s2, s3, s4, g1)

    def tearDown(self):
        CallbackHandler._instance = None

    def test_instanciation_cli(self):
        '''Test the instanciation of the CLI'''
        self.assertTrue(CommandLineInterface())

    def test_execute_retcode_unknow_exception(self):
        '''
        Test if the method execute returns 12 if an unknown exception is raised
        '''
        cli = CommandLineInterface()
        self.assertRaises(TypeError, cli.execute, [8, 9])

    def test_command_line_default_variables(self):
        '''Test default values of automatic variables from command line.'''
        cli = CommandLineInterface()
        cli.execute(['status'])
        manager = service_manager_self()
        self.assertEqual(manager.variables['SELECTED_NODES'], '')
        self.assertEqual(manager.variables['EXCLUDED_NODES'], '')

    def test_command_line_variables(self):
        '''Test automatic variables from command line options.'''
        cli = CommandLineInterface()
        cli.execute(['status', '-n', 'foo[1-5]', '-x', 'foo8'])
        manager = service_manager_self()
        self.assertEqual(manager.variables['SELECTED_NODES'], 'foo[1-5]')
        self.assertEqual(manager.variables['EXCLUDED_NODES'], 'foo8')

    # ---

    def test_execute_multiple_services(self):
        '''Test execution of S2 and G1 at the same time'''
        cli = CommandLineInterface()
        retcode = cli.execute(['S2', 'G1', 'start', '-d', '-x', 'fortoy8'])
        manager = service_manager_self()
        self.assertEqual(retcode, RC_OK)
        self.assertEqual(manager.entities['S2'].status, DONE)
        self.assertEqual(manager.entities['G1'].status, DONE)

    def test_execute_multiple_services_reverse(self):
        '''Test reverse execution of S2 and G1 at the same time'''
        cli = CommandLineInterface()
        retcode = cli.execute(['S2', 'G1', 'stop', '-d', '-x', 'fortoy8'])
        manager = service_manager_self()
        self.assertEqual(retcode, RC_ERROR)
        self.assertEqual(manager.entities['S1'].status, DONE)
        self.assertEqual(manager.entities['S3'].status, ERROR)
        self.assertEqual(manager.entities['S2'].status, DONE)
        self.assertEqual(manager.entities['G1'].status, DEP_ERROR)

    def test_execute_overall_graph(self):
        '''Test no services required so make all'''
        cli = CommandLineInterface()
        retcode = cli.execute(['start', '-d', '-x', 'fortoy8'])
        manager = service_manager_self()
        self.assertEqual(retcode, RC_ERROR)
        self.assertEqual(manager.entities['S1'].status, DEP_ERROR)
        self.assertEqual(manager.entities['S2'].status, DONE)
        self.assertEqual(manager.entities['S3'].status, ERROR)
        self.assertEqual(manager.entities['S4'].status, DONE)
        self.assertEqual(manager.entities['G1'].status, DONE)

    def test_execute_overall_graph_reverse(self):
        '''Test no services required so make all reverse'''
        cli = CommandLineInterface()
        retcode = cli.execute(['stop', '-d', '-x', 'fortoy8'])
        manager = service_manager_self()
        self.assertEqual(retcode, RC_ERROR)
        self.assertEqual(manager.entities['S1'].status, DONE)
        self.assertEqual(manager.entities['S2'].status, DONE)
        self.assertEqual(manager.entities['S3'].status, ERROR)
        self.assertEqual(manager.entities['S4'].status, DEP_ERROR)
        self.assertEqual(manager.entities['G1'].status, DEP_ERROR)

class CLIOutputTests(TestCase):
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

        ConfigParser.DEFAULT_FIELDS['config_dir']['value'] = ''
        ConfigParser.CONFIG_PATH = '/dev/null'

        ServiceManager._instance = None 
        manager = service_manager_self()

        svc1 = Service('S1')
        svc1.desc = 'I am the service S1'
        svc2 = Service('S2')
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
        manager.register_services(svc1, svc2, svc3, group1)

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

    def test_execute_std_verbosity(self):
        '''Check CLI execute() (no option)'''
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
        '''Check CLI execute() (-v)'''
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
        '''Check CLI execute() (-vv)'''
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
        '''Check CLI execute() (-d)'''
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
        '''
        Test if the method execute returns 9 if a known exception is raised
        '''
        self._output_check(['S6', 'start'], RC_EXCEPTION,
"""""",
"""[00:00:00] ERROR    - Undefined service [S6]
""")


class CommandLineOutputTests(TestCase):
    '''Tests cases of the command line output'''

    def setUp(self):
        '''
        Set up the graph of services within the service manager

        Graph
                              _ start
           group --> service /
                             `- stop
        '''

        ConfigParser.DEFAULT_FIELDS['config_dir']['value'] = ''
        ConfigParser.CONFIG_PATH = '/dev/null'

        ServiceManager._instance = None
        manager = service_manager_self()

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
        manager.register_services(group, service)

        # Setup stdout as a MyOutput file
        self.oldstdout = sys.stdout
        sys.stdout = MyOutput()
        self.oldstderr = sys.stderr
        sys.stderr = MyOutput()

    def tearDown(self):
        '''Restore sys.stdout and sys.stderr'''
        sys.stdout = self.oldstdout
        sys.stderr = self.oldstderr
        CallbackHandler._instance = None

    def _output_check(self, args, expected):
        """ Test Milcheck output with:
             - expected: expected output
             - args: command line args for cli.execute
        """
        cli = CommandLineInterface()
        cli._console.cleanup = False
        cli._console._term_width = 77
        cli.execute(args)
        msg = sys.stdout.getvalue()
        self.assertEqual(expected, msg)

    def test_command_output_help(self):
        '''Test command line help output'''
        if sys.version_info[0] == 2 and sys.version_info[1] < 5:
            self._output_check([],
"""usage: nosetests [options] [SERVICE...] ACTION

options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         Increase or decrease verbosity
  -d, --debug           Set debug mode and maximum verbosity
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
            self._output_check([],
"""Usage: nosetests [options] [SERVICE...] ACTION

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         Increase or decrease verbosity
  -d, --debug           Set debug mode and maximum verbosity
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
        self._output_check(['-c', '../conf/base'],
"""No actions specified, checking configuration...
../conf/base seems good
""" )

    def test_command_output_ok(self):
        '''Test command line output with all actions OK'''
        self._output_check(['ServiceGroup', 'start'],
"""ServiceGroup.service - I am the service                           [    OK   ]
ServiceGroup                                                      [    OK   ]
""")

    def test_command_output_ok_verbose2(self):
        '''Test command line output with local action OK in verbose x2'''
        self._output_check(['ServiceGroup', 'start', '-vv'],
"""start ServiceGroup.service on localhost
 > /bin/true
start ServiceGroup.service ran in 0.00 s
 > localhost exited with 0
ServiceGroup.service - I am the service                           [    OK   ]
ServiceGroup                                                      [    OK   ]
""")

    def test_command_output_summary_ok(self):
        '''Test command line output with summary and all actions OK'''
        self._output_check(['ServiceGroup', 'start', '-s'],
"""ServiceGroup.service - I am the service                           [    OK   ]
ServiceGroup                                                      [    OK   ]

 SUMMARY - 1 action (0 failed)
""")

    def test_command_output_error(self):
        '''Test command line output with all actions FAILED'''
        self._output_check(['ServiceGroup', 'stop'],
"""stop ServiceGroup.service ran in 0.00 s
 > localhost exited with 1
ServiceGroup.service - I am the service                           [  ERROR  ]
ServiceGroup                                                      [DEP_ERROR]
""")

    def test_command_output_summary_error(self):
        '''Test command line output with summary and all actions FAILED'''
        self._output_check(['ServiceGroup', 'stop', '-s'],
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
        self._output_check(['ServiceGroup', 'timeout'],
"""timeout ServiceGroup.service ran in 0.00 s
 > localhost has timeout
ServiceGroup.service - I am the service                           [ TIMEOUT ]
ServiceGroup                                                      [DEP_ERROR]
""")

    def test_command_output_dist_timeout(self):
        '''Test command line output with distant timeout'''
        self.service.add_action(Action('dist_timeout', HOSTNAME,
                                       command='/bin/sleep 1', timeout=0.1))
        self._output_check(['ServiceGroup', 'dist_timeout'],
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
        self._output_check(['ServiceGroup', 'multiple_dist_timeout'],
"""multiple_dist_timeout ServiceGroup.service ran in 0.00 s
 > HOSTNAME,localhost has timeout
ServiceGroup.service - I am the service                           [ TIMEOUT ]
ServiceGroup                                                      [DEP_ERROR]
""")
