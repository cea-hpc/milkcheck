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
This module implements several classes to handle all command line interface
with MilkCheck.

It communicates with MilkCheck Engine and handles output display and terminal
specificities.
'''

# classes
import fcntl, termios, struct, os, sys, traceback, threading, select
from signal import SIGINT
from ClusterShell.NodeSet import NodeSet
from MilkCheck.Callback import CoreEvent, call_back_self
from MilkCheck.UI.OptionParser import McOptionParser
from MilkCheck.Engine.Action import Action, action_manager_self
from MilkCheck.Engine.Service import Service
from MilkCheck.ServiceManager import ServiceManager
from MilkCheck.config import ConfigParser, ConfigError

# Exceptions
from yaml.scanner import ScannerError
from MilkCheck.Engine.ServiceGroup import ServiceNotFoundError
from MilkCheck.UI.OptionParser import InvalidOptionError
from MilkCheck.Engine.BaseEntity import UnknownDependencyError
from MilkCheck.Engine.BaseEntity import InvalidVariableError
from MilkCheck.Engine.BaseEntity import UndefinedVariableError
from MilkCheck.Engine.BaseEntity import VariableAlreadyExistError
from MilkCheck.Engine.BaseEntity import DependencyAlreadyReferenced
from MilkCheck.Engine.BaseEntity import IllegalDependencyTypeError
from MilkCheck.Engine.Service import ActionNotFoundError

# Symbols
from MilkCheck.Engine.BaseEntity import WARNING, SKIPPED, LOCKED
from MilkCheck.Engine.BaseEntity import TIMEOUT, ERROR, DEP_ERROR, DONE
from MilkCheck.Engine.BaseEntity import NO_STATUS, WAITING_STATUS

# Definition of retcodes
RC_OK = 0
RC_WARNING = 3
RC_ERROR = 6
RC_EXCEPTION = 9
RC_UNKNOWN_EXCEPTION = 12


MAXTERMWIDTH = 120

class Terminal(object):
    '''Allow the displayer to get informations from the terminal'''

    @classmethod
    def _ioctl_gwinsz(cls, fds):
        '''Try to determine terminal width'''
        try:
            data = fcntl.ioctl(fds, termios.TIOCGWINSZ, '1234')
            crt = struct.unpack('hh', data)
        except (IOError, struct.error, ValueError):
            return None
        return crt

    @classmethod
    def size(cls):
        '''Return a tuple which contain the terminal size or default size'''
        crt = cls._ioctl_gwinsz(0) or cls._ioctl_gwinsz(1) or \
             cls._ioctl_gwinsz(2)
        if not crt:
            try:
                fds = os.open(os.ctermid(), os.O_RDONLY)
                crt = cls._ioctl_gwinsz(fds)
                os.close(fds)
            except OSError:
                pass
        if not crt:
            crt = (os.environ.get('LINES', 25), os.environ.get('COLUMNS', 80))
        return int(crt[1]), int(crt[0])

    @classmethod
    def isatty(cls):
        '''Determine if the current terminal is teletypewriter'''
        return sys.stdout.isatty() and sys.stderr.isatty()

    @classmethod
    def isafgtty(cls, descriptor):
        '''
        Return True if 'descriptor' is a foreground tty
        '''
        return descriptor.isatty() and \
               os.tcgetpgrp(descriptor.fileno()) == os.getpgrp()

    @classmethod
    def isinteractive(cls):
        '''
        Return True if Terminal is interactive
        '''
        return cls.isafgtty(sys.stdin) and cls.isafgtty(sys.stdout)

class ConsoleDisplay(object):
    '''
    ConsoleDisplay provides methods allowing the CLI to print
    formatted messages on STDOUT.
    '''
    _COLORS = {
                'GREEN': '\033[0;32m%s\033[0m',
                'YELLOW': '\033[0;33m%s\033[0m',
                'RED': '\033[0;31m%s\033[0m',
                'MAGENTA': '\033[0;35m%s\033[0m',
                'CYAN': '\033[0;36m%s\033[0m'
              }
    _LARGEST_STATUS = max([len(status) \
         for status in (SKIPPED, WARNING, TIMEOUT, ERROR, DEP_ERROR, DONE)])

    def __init__(self):
        width = Terminal.size()[0]
        self._term_width = width
        self._pl_width = 0
        self._color = Terminal.isatty()
        self._show_running = Terminal.isatty()
        # Cleanup line before printing a message (see output)
        self.cleanup = True
        # Compute the number of escape characters
        self.escape = 0

    def string_color(self, strg, color):
        '''Return a string formatted with a special color'''
        if self._color:
            self.escape += len(self._COLORS[color]) - 2
            return '%s' % self._COLORS[color] % strg
        else:
            return '%s' % strg

    def print_running_tasks(self):
        '''Rewrite the current line and print the current running tasks'''
        rtasks = [t.parent.name for t in action_manager_self().running_tasks]
        if rtasks and self._show_running:
            tasks_disp = '[%s]' % NodeSet.fromlist(rtasks)
            width = min(self._pl_width, self._term_width)

            # truncate display to avoid buggy display when the length on
            # the displayed tasks is bigger than the screen width
            if len(tasks_disp) >= self._term_width:
                tasks_disp = "%s...]" % tasks_disp[:self._term_width - 4]

            eol = ' ' * (width - len(tasks_disp))
            if not self.cleanup:
                eol = ''

            sys.stderr.write('%s%s\r' % (tasks_disp, eol))
            sys.stderr.flush()
            self._pl_width = len(tasks_disp)

    def output(self, line, raw=False):
        '''Rewrite the current line and display line and jump to the next one'''
        if raw:
            sys.stdout.write('%s\n' % line)
            sys.stdout.flush()
            return
        width = min(self._pl_width, self._term_width)
        # Compute spaces at the end of the line to remove previous garbage
        # on stderr (escape characters are ignored)
        eol = ' ' * (width - len(line) + self.escape)
        if not self._show_running:
            eol = ''
        sys.stdout.write('%s%s\n' % (line, eol))
        sys.stdout.flush()
        self._pl_width = len(line)
        self.escape = 0

    def print_status(self, entity):
        '''Remove current line and print the status of an entity on STDOUT'''
        # On very wide terminal, do not put the status too far away
        msg_width = min(self._term_width, MAXTERMWIDTH) - \
                                                     (self._LARGEST_STATUS + 4)
        line = '%%-%ds%%%ds' % (msg_width, (self._LARGEST_STATUS + 4))

        # Label w/o description
        label = entity.longname()
        if len(label) > msg_width:
            label = "%s..." % label[:msg_width - 3 ]

        if entity.status in (TIMEOUT, ERROR, DEP_ERROR):
            line = line % (label,
                '[%s]' % \
                    self.string_color(
                    entity.status.center(self._LARGEST_STATUS), 'RED'))
        elif entity.status in (WARNING, SKIPPED):
            line = line % (label,
                '[%s]' % \
                self.string_color(entity.status.center(self._LARGEST_STATUS),
                                  'YELLOW'))
        elif entity.status is DONE:
            line = line % (label,
                '[%s]' % \
                self.string_color('OK'.center(self._LARGEST_STATUS),
                                  'GREEN'))
        else:
            line = line % (label, '[%s]' % entity.status)
        self.output(line)

    def print_summary(self, actions, report='default'):
        """Print the errors summary of the array actions"""
        lines = []

        errors = 0
        others = 0
        to_spell = 'action'
        error_nodes = NodeSet()
        all_error_nodes = NodeSet()
        all_nodes = NodeSet()

        for ent in actions:
            error_nodes.clear()
            errs = NodeSet(ent.nodes_error())
            timeouts = NodeSet(ent.nodes_timeout())
            all_nodes.add(ent.target)

            if ent.status in (TIMEOUT, ERROR, DEP_ERROR):
                error_nodes.add(errs)
                error_nodes.add(timeouts)
                lines.append(" + %s" % self.string_color(
                                                ent.longname().strip(), 'RED'))
                if report == 'full':
                    msg = "    %s: %s\n" % (self.string_color("Target",
                                                              'YELLOW'),
                                          error_nodes)
                    msg += "    %s: %s" % (self.string_color("Command",
                                                             'YELLOW'),
                                          ent.worker.command)
                    lines.append(msg)

                errors += 1
            elif ent.status not in (SKIPPED, LOCKED):
                others += 1
            all_error_nodes.add(error_nodes)

        # manage 'action(s)' spelling
        if (errors + others) > 1:
            to_spell += 's'

        header = "\n %s - %s %s (%s failed)" % (
                       self.string_color('Summary'.upper(), 'MAGENTA'),
                       self.string_color('%d' % (errors + others), 'CYAN'),
                       to_spell,
                       self.string_color(errors, (errors and 'RED' or 'GREEN')))
        lines.insert(0, header)
        good_nodes = all_nodes - all_error_nodes
        if report == 'full' and good_nodes:
            lines.append(" + %s" % self.string_color('Success on all services',
                                                     'GREEN'))
            lines.append("    %s" % good_nodes)
        self.output("\n".join(lines), raw=True)

    def print_action_command(self, action):
        '''Remove the current line and write informations about the command'''
        line = '%s %s %s %s\n > %s' % \
            (self.string_color(action.name, 'MAGENTA'),
             action.parent.fullname(),
             self.string_color('on', 'MAGENTA'), action.target or 'localhost',
             self.string_color(action.command, 'CYAN'))
        self.output(line)

    def __gen_action_output(self, iterbuf, iterrc, timeouts, error_only):
        '''Display command result from output and retcodes.'''

        # Build the list of non-zero rc nodes
        retcodes = list(iterrc)
        ok_nodes = NodeSet.fromlist((nds for rc, nds in retcodes if rc == 0))

        output = []
        for out, nodes in iterbuf:
            if error_only:
                nodes = NodeSet(nodes) - ok_nodes
            if nodes and out:
                for lbuf in out.splitlines():
                    output.append(' > %s: %s' %
                                  (self.string_color(nodes, 'CYAN'), lbuf))

        for retcode, nodes in retcodes:
            if retcode == 0 and not error_only:
                output.append(' > %s exited with %s' %
                              (self.string_color(nodes, 'CYAN'),
                               self.string_color(retcode, 'GREEN')))
            elif retcode != 0:
                output.append(' > %s exited with %s' %
                              (self.string_color(nodes, 'CYAN'),
                               self.string_color(retcode, 'RED')))
        if len(timeouts):
            output.append(' > %s has %s' %
                          (self.string_color(timeouts, 'CYAN'),
                           self.string_color('timeout', 'RED')))
        return output

    def print_action_results(self, action, error_only=False):
        '''Remove the current line and write grouped results of an action'''
        line = ['%s %s ran in %.2f s' % \
            (self.string_color(action.name, 'MAGENTA'),
             action.parent.fullname(),
             action.duration)]
        buffers = []
        retcodes = []
        timeout = NodeSet()
        # Local action
        if action.worker.current_node is None:
            buffers = [(action.worker.read(), 'localhost')]
            if action.worker.did_timeout():
                timeout.add('localhost')
            if action.worker.retcode() is not None:
                retcodes.append((action.worker.retcode(),'localhost'))
        # Remote action
        else:
            buffers = action.worker.iter_buffers()
            retcodes = action.worker.iter_retcodes()
            timeout = NodeSet.fromlist(action.worker.iter_keys_timeout())

        line += self.__gen_action_output(buffers, retcodes, timeout, error_only)
        self.output("\n".join(line))

    def print_delayed_action(self, action):
        '''Display a message specifying that this action has been delayed'''
        line = '%s %s %s %s s' % \
            (self.string_color(action.name, 'MAGENTA'),
             action.parent.fullname(),
             self.string_color('will fire in', 'MAGENTA'),
             action.delay)
        self.output(line)

    def print_manager_status(self, manager):
        ''' Display current ActionManager status'''
        msg = self.string_color("\nActions in progress\n", 'MAGENTA')
        for act in manager.running_tasks:
            if act.status in (NO_STATUS, WAITING_STATUS):
                target = str(act.pending_target) or 'localhost'
                # Display nodeset count if needed (greather than 2)
                nscount = ''
                if len(act.pending_target) > 1:
                    nscount = " (%d)" % len(act.pending_target)
                # Manage delayed status
                delayed = ''
                if act.tries == 0 and act.delay:
                    delayed = " (delayed for %ss)" % act.delay
                # Manage line length
                label = act.fullname()
                name_len = len(" > %s on " % label)
                # Compute the max label name. We want to have at least the
                # service name and the start of the nodes where it is running.
                max_len = self._term_width - len (" > service... on node...")
                if name_len > max_len:
                    label = "%s..." % label[:max_len]
                    name_len = len(" > %s on " % label)
                # Truncate the target if the line is greater than the terminal
                # width
                if name_len + len(target) + len(nscount) + len(delayed) \
                                                        > self._term_width:
                    tgt_len = self._term_width - name_len - 4 - len(nscount) \
                                                        - len(delayed)
                    target = "%s..." % target[:tgt_len]
                msg += " > %s%s on %s%s\n" % (
                                 self.string_color(label, 'YELLOW'),
                                 self.string_color(delayed, 'YELLOW'),
                                 self.string_color(target, 'CYAN'), nscount)
        self.output(msg)

class InteractiveThread(threading.Thread):
    '''
    Separated thread to manage user input
    '''
    def __init__(self, console):
        '''Setup console to manage display on user input'''
        threading.Thread.__init__(self)
        self._console = console
        # _run_state and _run_ctl controls the thread termination
        self._run_state, self._run_ctl = os.pipe()
        self._watcher = select.poll()

    def _got_events(self):
        '''Poll stdin events'''
        return self._watcher.poll()

    def _flush_events(self):
        '''Flush stdin'''
        sys.stdin.readline()

    def _register(self, desc):
        '''Register file descriptor to watch'''
        self._watcher.register(desc, select.POLLIN  |
                                     select.POLLPRI |
                                     select.POLLERR |
                                     select.POLLHUP |
                                     select.POLLNVAL)

    def run(self):
        '''Poll stdin and print current running status if needed'''
        self._register(sys.stdin)
        self._register(self._run_state)
        runnable = True
        while(runnable):
            for (desc, event) in self._got_events():
                if event:
                    if desc == self._run_state:
                        # _run_state hangs up, stop the loop
                        runnable = False
                    elif event & (select.POLLIN | select.POLLPRI):
                        self._flush_events()
                        self._console.print_manager_status(
                                            action_manager_self())
                    # Unexpected or not wanted event
                    else:
                        print "Unexpected event on interactive thread"
                        runnable = False

    def join(self, timeout=None):
        '''Only join if thread is alive'''
        if self.isAlive():
            threading.Thread.join(self, timeout)

    def quit(self):
        '''Properly quit the thread'''
        os.close(self._run_ctl)

class CommandLine(CoreEvent):
    '''
    This class models the Command Line which is a CoreEvent. From
    this class you can get back events generated by the engine and send order
    to the ServiceManager.
    '''

    def __init__(self):
        CoreEvent.__init__(self)

        # Parser which reads the command line
        self._mop = None
        # Store the options parsed
        self._options = None
        # Store the configuration parsed
        self._conf = None
        # Store the arguments parsed
        self._args = None
        # Store executed actions
        self.actions = []
        # Displayer
        self._console = ConsoleDisplay()
        # Store interactive mode
        self.interactive = Terminal.isinteractive()

        # Useful for tests
        self.manager = None

        self._logger = ConfigParser.install_logger()

        call_back_self().attach(self)
        self.inter_thread = InteractiveThread(self._console)

    def execute(self, command_line):
        '''
        Ask for the manager to execute orders given by the command line.
        '''
        self._mop = McOptionParser()
        self._mop.configure_mop()
        retcode = RC_OK

        try:
            (self._options, self._args) = self._mop.parse_args(command_line)

            self._conf = ConfigParser(self._options)

            # Configure ActionManager
            action_manager_self().default_fanout = self._conf['fanout']
            action_manager_self().dryrun = self._conf['dryrun']

            manager = self.manager or ServiceManager()
            # Case 0: build the graph
            if self._conf.get('graph', False):
                manager.load_config(self._conf['config_dir'])
                # Deps graph generation
                self._console.output(manager.output_graph(self._args,
                                     self._conf.get('excluded_svc', [])))
            # Case 1 : call services referenced in the manager with
            # the required action
            elif self._args:
                # Compute all services with the required action
                services = self._args[:-1]
                action = self._args[-1]

                # Create a thread in interactive mode to manage
                # current running status
                if self.interactive:
                    self.inter_thread.start()

                # Run tasks
                manager.call_services(services, action, conf=self._conf)
                retcode = self.retcode()

                if self._conf.get('report', 'no').lower() != 'no':
                    r_type = self._conf.get('report','default')
                    self._console.print_summary(self.actions, report=r_type)

            # Case 2 : Check configuration
            elif self._conf.get('config_dir', False):
                self._console.output("No actions specified, "
                                     "checking configuration...")
                manager.load_config(self._conf['config_dir'])
                self._console.output("%s seems good" % self._conf['config_dir'])
            # Case 3: Nothing to do so just print MilkCheck help
            else:
                self._mop.print_help()
        except (ServiceNotFoundError, 
                ActionNotFoundError,
                InvalidVariableError,
                UndefinedVariableError,
                VariableAlreadyExistError,
                DependencyAlreadyReferenced,
                UnknownDependencyError,
                IllegalDependencyTypeError,
                ConfigError,
                ScannerError), exc:
            self._logger.error(str(exc))
            retcode = RC_EXCEPTION
        except InvalidOptionError, exc:
            self._logger.critical('Invalid options: %s\n' % exc)
            self._mop.print_help()
            retcode = RC_EXCEPTION
        except KeyboardInterrupt, exc:
            self._logger.error('Keyboard Interrupt')
            retcode = (128 + SIGINT)
        except ScannerError, exc:
            self._logger.error('Bad syntax in config file :\n%s' % exc)
            retcode = RC_EXCEPTION
        except ImportError, exc:
            self._logger.error('Missing python dependency: %s' % exc)
            for line in traceback.format_exc().splitlines()[-3:-1]:
                self._logger.error(line)
            retcode = RC_EXCEPTION
        except Exception, exc:
            # In high verbosity mode, propagate the error
            if (not self._conf or self._conf.get('verbosity') >= 5):
                traceback.print_exc(file=sys.stdout)
            else:
                self._logger.error('Unexpected Exception : %s' % exc)
            retcode = RC_UNKNOWN_EXCEPTION

        # Quit the interactive thread
        self.inter_thread.quit()
        self.inter_thread.join()

        return retcode

    def retcode(self):
        '''
        Determine a retcode from a the last point of the graph
            RC_OK = 0: Everything went as we expected
            RC_WARNING = 3: At least one service status is WARNING
                            and all others status is OK
            RC_ERROR = 6: At least one service status is ERROR

        Handled by self.execute :
            RC_EXCEPTION = 9: User error (options or configuration)
            RC_UNKNOWN_EXCEPTION = 12: Internal error (this is probably a bug)
        '''
        if self.manager.status in (DEP_ERROR, ERROR):
            return RC_ERROR
        elif self.manager.has_warnings():
            return RC_WARNING
        else:
            return RC_OK

    def ev_started(self, obj):
        '''
        Something has started on the object given as parameter. This migh be
        the beginning of a command one a node, an action or a service.
        '''
        if isinstance(obj, Action) and self._conf['verbosity'] >= 2:
            self._console.print_action_command(obj)
            self._console.print_running_tasks()
        elif isinstance(obj, Service) and self._conf['verbosity'] >= 1:
            self._console.print_running_tasks()

    def ev_complete(self, obj):
        '''
        Something is complete on the object given as parameter. This migh be
        the end of a command on a node,  an action or a service.
        '''
        if isinstance(obj, Action):
            self.actions.append(obj)
            if self._conf['verbosity'] >= 3 and obj.status != SKIPPED:
                self._console.print_action_results(obj)
                self._console.print_running_tasks()
            elif obj.status in (TIMEOUT, ERROR, DEP_ERROR) and \
                      self._conf['verbosity'] >= 1:
                self._console.print_action_results(obj,
                                           self._conf['verbosity'] == 1)
                self._console.print_running_tasks()
        elif isinstance(obj, Service) and self._conf['verbosity'] >= 1:
            self._console.print_running_tasks()

    def ev_status_changed(self, obj):
        '''
        Status of the object given as parameter. Actions or Service's status
        might have changed.
        '''
        if isinstance(obj, Service) and not (obj.status == SKIPPED and \
                               self._conf['verbosity'] < 3) and \
                               obj.status in (TIMEOUT, ERROR, DEP_ERROR, DONE,
                               WARNING, SKIPPED) and not obj.simulate:

            self._console.print_status(obj)
            self._console.print_running_tasks()

    def ev_delayed(self, obj):
        '''
        Object given as parameter has been delayed. This event is only raised
        when an action was delayed
        '''
        if isinstance(obj, Action) and self._conf['verbosity'] >= 3:
            self._console.print_delayed_action(obj)
            self._console.print_running_tasks()

    def ev_trigger_dep(self, obj_source, obj_triggered):
        '''
        obj_source/obj_triggered might be an action or a service. This
        event is raised when the obj_source triggered another object. Sample :
        Action A triggers Action B
        Service A triggers Service B
        '''
        pass

    def ev_finished(self, obj):
        '''
        Finalize milcheck call
        '''
        pass
