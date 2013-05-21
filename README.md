MilkCheck
=========

MilkCheck is a Python-based distributed, highly parallel and flexible service manager. It runs commands across various servers, based on dependencies between them, and offers a compact execution summary. It aims to manage service starting and checking on very large number of servers, like in HPC world. It can run tens of thousands of commands across thousand servers in very short time.

Requirements
------------

* Python 2.4+
* ClusterShell 1.6+

Installation
------------

From source:

    # python setup.py install
    # mkdir -p /etc/milkcheck/conf
    # cp conf/milkcheck.conf /etc/milkcheck
    # cp -r conf/samples /etc/milkcheck/conf

Or, build RPM and install it:

    $ make rpm
    $ rpm -ivh RPMBUILD/RPMS/noarch/milkcheck-*.rpm

Tests
-----

MilkCheck has its own test suite which could be used to check for issue when making patches or testing its correct behaviour on your system.
Before running tests, you must verify you can connect, through SSH to your local machine, non-interactively, without password. Try:

    $ ssh -o PasswordAuthentication=no $HOSTNAME echo OK
    $ ssh -o PasswordAuthentication=no localhost echo OK

You must install [python nose](https://pypi.python.org/pypi/nose) v0.11+, then run:

    $ make test

Documentation
-------------

See MilkCheck man page for command usage and `conf/samples/example.yaml` for file configuration documentation.

Quick start
-----------

Install MilkCheck (see above)

Create your first configuration file in `/etc/milkcheck/conf`

    $ vim /etc/milkcheck/conf/first.yaml

Create a local service, running the classical Hello World.

    services:
        hello:
            actions:
                start:
                   cmd: echo Hello World

Check this configuration, running `milkcheck` without option

    $ milkcheck
    No actions specified, checking configuration...
    /etc/milkcheck/conf seems good

If everything is fine, launch the `start` action

    $ milkcheck start
    hello                                           [    OK   ]

If you need to run a service on remote nodes, simply add a `target` option:

    services:
        hello:
            actions:
                start:
                   cmd: echo Hello World
        crond:
            target: foo[1-10]
            actions:
                start:
                   cmd: /etc/init.d/crond start

Launch the `start` action again

    $ milkcheck start
    hello                                           [    OK   ]
    crond                                           [    OK   ]

Check `conf/sample/example.yaml` for all possibilities.


Website
-------

Latest source, bugtracker and information could be retrieve from MilkCheck website:

https://github.com/cea-hpc/milkcheck/

License
-------

See Licence_CeCILL_V2-en.txt (english version) or Licence_CeCILL_V2-fr.txt (french version).

Authors
-------

See `AUTHORS`.
