#!/usr/bin/env python

import sys
sys.path.append('lib')

from setuptools import setup, find_packages
from MilkCheck import __version__

setup(name='MilkCheck',
      version=__version__,
      license='CeCILL',
      description='Parallel command execution manager',
      author='Aurelien Degremont',
      author_email='aurelien.degremont@cea.fr',
      package_dir={'': 'lib'},
      packages=find_packages('lib'),
      scripts=['scripts/milkcheck']
     )
