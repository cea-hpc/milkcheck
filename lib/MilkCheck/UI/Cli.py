# Copyright CEA (2011)
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

'''
This module contains the UserView class definition.
'''

# classes
import logging
import logging.config
from time import sleep
from sys import stdout
from ClusterShell.Worker.Popen import WorkerPopen
from MilkCheck.UI.UserView import UserView
from MilkCheck.UI.OptionParser import McOptionParser
from MilkCheck.UI.OptionParser import InvalidOptionError
from MilkCheck.Engine.Action import Action
from MilkCheck.Engine.Service import Service, ActionNotFoundError
from MilkCheck.ActionManager import action_manager_self
from MilkCheck.ServiceManager import service_manager_self
from MilkCheck.ServiceManager import ServiceNotFoundError
from MilkCheck.Engine.BaseEntity import DONE_WITH_WARNINGS
from MilkCheck.Engine.BaseEntity import TIMED_OUT, TOO_MANY_ERRORS, ERROR, DONE

class ConsoleDisplay(object):
    '''
    ConsoleDisplay provides methods allowing the CLI to print
    formatted messages on STDOUT.
    '''
    _COLORS = {
                'GREEN': '\033[1;32m%s\033[0m',
                'YELLOW': '\033[1;33m%s\033[0m',
                'RED': '\033[1;31m%s\033[0m',
                'MAGENTA': '\033[95m%s\033[0m',
                'CYAN': '\033[94m%s\033[0m'
              }

    def __init__(self):
        stdout.write('\n')
        stdout.flush()
        self.pl_width = 0

    def string_color(self, strg, color):
        '''Return a string formatted with a special color'''
        return '%s' % self._COLORS[color] % strg 

    def print_version(self, version):
        '''Display the current version of MilkCheck'''
        stdout.write(version)
        stdout.flush()

    def print_running_tasks(self):
        '''Remove current line and print the current running tasks'''
        rtasks = [t.parent.name for t in action_manager_self().running_tasks]
        if rtasks:
            tasks_disp = '[%s]' % ','.join(rtasks)
            stdout.write('\r%s\r%s' % (self.pl_width*' ', tasks_disp))
            stdout.flush()
            self.pl_width = len(tasks_disp)

    def print_status(self, entity, colors=True):
        '''Remove current line and print the status of an entity onSTDOUT'''
        line = ''
        if entity.status in (TIMED_OUT, TOO_MANY_ERRORS, ERROR) and colors:
            line = '\r%-50s%30s\n' % (entity.name, 
            '[%s]' % self.string_color(entity.status, 'RED'))
        elif entity.status is DONE_WITH_WARNINGS and colors:
            line = '\r%-50s%30s\n' % (entity.name, 
            '[%s]' % self.string_color('WARNING', 'YELLOW'))
        elif entity.status is DONE and colors:
            line = '\r%-50s%30s\n' % (entity.name, 
            '[%s]' % self.string_color('OK', 'GREEN'))
        else:
            line = '\r%-50s%30s\n' % (entity.name, '[%s]' % entity.status)
        self.pl_width = len(line)
        stdout.write(line)
        stdout.flush()

    def print_action_command(self, action):
        '''Remove the current line and write informations about the command'''
        line = ''
        if action.target:
            line = '\r%s %s %s %s\n > %s \n' % \
                (self.string_color(action.name, 'MAGENTA'),
                 action.parent.name,
                 self.string_color('on', 'MAGENTA'),
                 action.resolve_property('target'), 
                 self.string_color(
                 action.resolve_property('command'), 'CYAN'))
        else:
            line = '\r%s %s %s localhost \n > %s \n' % \
                (self.string_color(action.name, 'MAGENTA'),
                 action.parent.name,
                 self.string_color('on', 'MAGENTA'), 
                 self.string_color(
                 action.resolve_property('command'), 'CYAN'))
        self.pl_width = len(line)
        stdout.write(line)
        stdout.flush()

    def print_action_results(self, action):
        '''Remove the current line and write grouped results of an action'''
        line = '\r%s %s %s %.2f s' % \
                (self.string_color(action.name, 'MAGENTA'),
                 action.parent.name,
                 self.string_color('ran in', 'MAGENTA'),
                 action.duration)
        # Local action
        if isinstance(action.worker, WorkerPopen):
            output = None
            if action.worker.read():
                output = '\n > %s : %s\n > %s : %d' % \
                    (self.string_color('localhost', 'CYAN'), 
                     action.worker.read(),
                     self.string_color('exit code', 'CYAN'), 
                     action.worker.retcode())
            else:
                output = '\n > %s > %s : %d' % \
                    (self.string_color('localhost', 'CYAN'),
                     self.string_color('exit code', 'CYAN'), 
                     action.worker.retcode())
            line = '%s%s\n' % (line, output)
        # Remote action
        else:
            output = None
            for out, nodes in action.worker.iter_buffers():
                output = '\n > %s : %s\n > %s : %d' % \
                    (self.string_color(nodes, 'CYAN'), out,
                        self.string_color('exit code', 'CYAN'),
                        action.worker.node_retcode(nodes[0]))
                line = '%s%s\n' % (line, output)
            for rc, nodes in action.worker.iter_retcodes():
                output = '\n > %s \n > %s : %d' % \
                (self.string_color(nodes, 'CYAN'),
                    self.string_color('exit code', 'CYAN'), rc)
                line = '%s%s\n' % (line, output)
        self.pl_width = len(line)
        stdout.write(line)
        stdout.flush()

class CommandLineInterface(UserView):
    '''
    This class models the Command Line Interface which is a UserView. From
    this class you can get back events generated by the engine and send order
    to the ServiceManager.
    '''

    def __init__(self):
        UserView.__init__(self)
        # Parser which reads the command line
        self._mop = None
        # Store the options parsed
        self._options = None
        # Store the arguments parsed
        self._args = None
        # Displayer
        self._console = ConsoleDisplay()
        # Profiling mode (help in unit tests)
        self.profiling = False
        # Used in profiling mode
        # Each counter match to a verbosity level
        self.count_low_verbmsg = 0
        self.count_average_verbmsg = 0
        self.count_high_verbmsg = 0

    def execute(self, command_line):
        '''
        Ask for the manager to execute orders given by the command line.
        '''
        watcher = logging.getLogger('watcher')
        self._mop = McOptionParser()
        self._mop.configure_mop()
        try:
            (self._options, self._args) = self._mop.parse_args(command_line)
        except InvalidOptionError, exc:
            watcher.error('%s' % exc)
            self._mop.print_help()
        else:
            manager = service_manager_self()
            self.count_low_verbmsg = 0
            self.count_average_verbmsg = 0
            self.count_high_verbmsg = 0
            # Case 1 : call services referenced in the manager with
            # the required action
            if self._args:
                try:
                    # Compute all services with the required action
                    if len(self._args) == 1:
                        manager.call_services(None, self._args[0],
                                opts=self._options)
                    else:
                        manager.call_services(
                            self._args[:len(self._args)-1], self._args[-1],
                                opts=self._options)
                except ServiceNotFoundError, exc:
                    watcher.error(' %s' % exc)
                except ActionNotFoundError, exc:
                    watcher.error(' %s' % exc)
            # Case 2 : we just display dependencies of one or several services
            elif self._options.print_servs:
                print 'TODO : Print service dependencies'
            # Case 3 : Just load another configuration
            elif self._options.config_dir:
                manager.load_config(self._options.config_dir)
            # Case 4: If version option detected so print version number
            elif self._options.version:
                self._console.print_version(self._options.version)
            else:
                self._mop.print_help()

    def ev_started(self, obj):
        '''
        Something has started on the object given as parameter. This migh be
        the beginning of a command one a node, an action or a service.
        '''
        sleep(0.5)
        if isinstance(obj, Action) and self._options.verbosity >= 2:
            self._console.print_action_command(obj)
            self._console.print_running_tasks()
            if self.profiling:
                self.count_average_verbmsg += 1
        elif isinstance(obj, Service) and self._options.verbosity >= 1:
            self._console.print_running_tasks()
            if self.profiling:
                self.count_low_verbmsg += 1

    def ev_complete(self, obj):
        '''
        Something is complete on the object given as parameter. This migh be
        the end of a command on a node,  an action or a service.
        '''
        sleep(0.5)
        if isinstance(obj, Action) and self._options.verbosity >= 3:
            self._console.print_action_results(obj)
            self._console.print_running_tasks()
            if self.profiling:
                self.count_high_verbmsg += 1
        elif isinstance(obj, Action) and \
            obj.status in (TIMED_OUT, TOO_MANY_ERRORS, ERROR) and \
                 self._options.verbosity >= 2:
            self._console.print_action_results(obj)
            self._console.print_running_tasks()
            if self.profiling:
                self.count_average_verbmsg += 1
        elif isinstance(obj, Service) and self._options.verbosity >= 1:
            self._console.print_running_tasks()
            if self.profiling:
                self.count_low_verbmsg += 1

    def ev_status_changed(self, obj):
        '''
        Status of the object given as parameter. Actions or Service's status
        might have changed.
        '''
        if isinstance(obj, Action) and self._options.verbosity >= 3 and \
            obj.status not in (TIMED_OUT, TOO_MANY_ERRORS, ERROR, DONE) and \
                not obj.parent.simulate:
            if self.profiling:
                self.count_average_verbmsg += 1
        elif isinstance(obj, Service) and self._options.verbosity >= 1 and \
            obj.status in (TIMED_OUT, TOO_MANY_ERRORS, ERROR, DONE) and \
                not obj.simulate:
            self._console.print_status(obj)
            self._console.print_running_tasks()
            if self.profiling:
                self.count_low_verbmsg += 1

    def ev_delayed(self, obj):
        '''
        Object given as parameter has been delayed. This event is only raised
        when an action was delayed
        '''
        if isinstance(obj, Action) and not obj.parent.simulate and \
            self._options.verbosity >= 3:
            if self.profiling:
                self.count_average_verbmsg += 1

    def ev_trigger_dep(self, obj_source, obj_triggered):
        '''
        obj_source/obj_triggered might be an action or a service. This
        event is raised when the obj_source triggered another object. Sample :
        Action A triggers Action B
        Service A triggers Service B
        '''
        pass

    def get_totalmsg_count(self):
        '''Sum all counter to know how many message the CLI got'''
        return  (self.count_low_verbmsg + \
                    self.count_average_verbmsg + \
                        self.count_high_verbmsg)

    total_msg_count = property(fget=get_totalmsg_count)