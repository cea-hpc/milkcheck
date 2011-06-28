#!/usr/bin/env python
# Copyright CEA (2011)
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This is the entry point of MilkCheck
"""
from sys import argv
from MilkCheck.UI.Cli import CommandLineInterface

if __name__ == "__main__":

    cli = CommandLineInterface()
    cli.execute(argv[1:])