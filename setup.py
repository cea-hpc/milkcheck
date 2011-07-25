#!/usr/bin/env python

from setuptools import setup, find_packages
import os

if not os.access('scripts/milkcheck', os.F_OK):
    os.symlink('milkcheck.py', 'scripts/milkcheck')

setup(name='MilkCheck',
      version='0.6',
      license='CEA-DAM',
      description='Parallele command execution manager',
      author='Aurelien Degremont',
      author_email='aurelien.degremont@cea.fr',
      package_dir={'': 'lib'},
      packages=find_packages('lib'),
      scripts=['scripts/milkcheck']
     )
