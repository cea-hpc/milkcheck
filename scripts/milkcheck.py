# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This is the entry point of MilkCheck
"""
from os import system
from sys import argv, exit
from MilkCheck.UI.Cli import CommandLineInterface

if __name__ == "__main__":

    system('clear')
    cli = CommandLineInterface()
    
    while True:
        args = raw_input('milkcheck$ ')
        cli.execute(args.split(' '))