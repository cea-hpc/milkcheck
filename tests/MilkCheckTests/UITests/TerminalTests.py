# Copyright CEA (2011)
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This modules defines the tests cases targeting the class Terminal
"""

import sys, fcntl, termios, struct, os
from unittest import TestCase
from MilkCheck.UI.Cli import Terminal

class MockTerminal(Terminal):
    '''Fake terminal class allowing us to tests'''

    @classmethod
    def _ioctl_gwinsz(cls, fds):
        return None
    
class TerminalTests(TestCase):
    '''Tests cases for the class Terminal'''
    
    def test_terminal_ioctl(self):
        '''Test Terminal system call always fails with a bad descriptor'''
        self.assertFalse(Terminal._ioctl_gwinsz(10))
        self.assertFalse(Terminal._ioctl_gwinsz(-1))

    def test_terminal_size_env(self):
        '''Test terminal size from environment variables'''
        os.environ['LINES'] = '20'
        os.environ['COLUMNS'] = '100'
        self.assertTrue(MockTerminal.size(), (20,100))
        del os.environ['LINES']
        del os.environ['COLUMNS']

    def test_terminal_size_default(self):
        '''Test default terminal size'''
        if 'LINES' in os.environ:
            del os.environ['LINES']
        if 'COLUMNS' in  os.environ:
            del os.environ['COLUMNS']
        self.assertEqual(MockTerminal.size(), (80, 25))