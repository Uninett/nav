=====================================
Using NAV with Docker for development
=====================================

.. highlight:: sh

Docker is a lightweight "virtualization" framework for creating isolated
environments, useful both in development and production.
For more information on Docker visit their homepage_ or read the documentation_.

Installing Docker
-----------------

Docker has updated documentation on how to install it for most Linux
distributions [*]_. Due to its dependency on a relatively new kernel (3.8+),
some distributions such as Debian stable will need to use a backports kernel.

.. Tip:: To avoid having to use sudo with docker commands it is recommended
         to add your user to the **docker** group. You may need to relogin for it to
         take effect.

Building the Docker image
-------------------------

First you will need to obtain the NAV source code.

The source contains a configuration file for `Docker Compose`_ to build a
suite of containers for PostgreSQL, Graphite and NAV itself. Simply run this
command to run everything::

    docker-compose up

.. Tip:: The first time you run this would be the perfect time to grab some
         coffee (and maybe redecorate your living room), as the initial build
         may take a while.


Using the container(s)
----------------------

The default Compose setup will expose the NAV web frontend on
http://localhost/ and the Graphite-web frontend on http://localhost:8000 .

You can access the inside of the NAV container (to control NAV daemons, adjust
the running config, or whatever) by running a bash shell inside it, like so::

  docker exec -ti nav_nav_1 /bin/bash

Happy hacking!


.. [*] See http://docs.docker.io/installation/#installation.
.. _homepage: http://docker.io
.. _documentation: http://docs.docker.io
.. _Docker Compose: https://docs.docker.com/compose/gettingstarted/
