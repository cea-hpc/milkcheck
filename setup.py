#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='MilkCheck',
      version='1.1',
      license='CeCILL',
      description='Parallel command execution manager',
      author='Aurelien Degremont',
      author_email='aurelien.degremont@cea.fr',
      package_dir={'': 'lib'},
      packages=find_packages('lib'),
      scripts=['scripts/milkcheck']
     )
