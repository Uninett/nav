=====================================
Using NAV with Docker for development
=====================================

.. highlight:: sh

Docker is a lightweight "virtualization" framework for creating isolated
environments, useful both in development and production.
For more information on Docker visit their homepage_ or read the documentation_.

Installing Docker and docker-compose
------------------------------------

Docker has updated documentation on how to install it for most Linux
distributions [*]_.

.. Tip:: To avoid having to use sudo with docker commands, it is recommended
         to add your user to the ``docker`` group. You may need to relogin for it to
         take effect.

Building the Docker image
-------------------------

First you will need to obtain the NAV source code.

The source contains a configuration file for `Docker Compose`_ to build a
suite of containers for PostgreSQL, Graphite and NAV itself. Simply run this
command to build and run everything::

    docker-compose up

.. Tip:: The first time you run this would be the perfect time to grab some
         coffee (and maybe redecorate your living room), as the initial build
         may take a while.


Using the container(s)
----------------------

The default Docker Compose setup will expose the NAV web frontend on
http://localhost/ and the Graphite-web frontend on http://localhost:8000 .

You can access the inside of the NAV container (to control NAV daemons using
the ``nav`` command, adjust the running config, or whatever) by running a bash
shell inside it, like so::

  docker-compose exec nav /bin/bash


Controlling processes inside the nav container
----------------------------------------------

The main ``nav`` container uses :program:`supervisord` to control multiple
processes. While the ``nav`` command can be used to control individual NAV
services, :program:`supervisorctl` can be used to control other processes used
within the development environment:

cron
  This is the regular system cron daemon, responsible for running recurring NAV
  tasks.

nav
  This is a one-time supervisor task to start all of NAV when the container
  starts.

sass-watcher
  This is a process that monitors the :file:`python/nav/web/sass/` subdirectory
  for changes, and re-runs ``python setup.py build_sass`` (i.e. rebuilding all
  the SASS-based stylesheets) on changes.

The individual logs of these program are typically found inside the ``nav``
container in the :file:`/var/log/supervisor/` directory. The NAV process logs
themselves are placed inside the :file:`/tmp/` directory inside the ``nav``
container.

Controlling log levels
----------------------

The log levels of various parts of NAV are controlled through the config file
:file:`/etc/nav/logging.conf` inside the containers. Please be aware that the
``nav`` and ``web`` containers do not share a configuration volume, so you may
need to make adjustments in either container, depending on your needs.


Happy hacking!


.. [*] See http://docs.docker.io/installation/#installation.
.. _homepage: http://docker.io
.. _documentation: http://docs.docker.io
.. _Docker Compose: https://docs.docker.com/compose/gettingstarted/
