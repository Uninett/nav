================================================================
Running just the database and graphite in Docker for development
================================================================

Instead of running everything including nav and a live rebuild of the docs via
``docker compose``, it is possible to just run the database and graphite via
``docker compose``.

There are helper commands in the makefile.

The docker compose config used is in ``tools/local-dev/docker-compose.yml``.

Make-helpers
============

``make local-setup``
--------------------

This sets up the docker containers and the virtualenv. The virtualenv used is
the one in ``.venv``, so if there alreday is a ``.venv`` (for instance from
using the heavy docker compose workflow). move it out of the way first.

``make local-up``
-----------------

Starts docker compose with the right config.

``make local-down``
-------------------

Shuts down the correct docker compose.

How to configure nav
====================

The etc-files are in ``.venv/etc/nav``.

How to test
===========

You can run tox directly, even for integration tests!

::

        $ tox

How to run nav
==============

::

        $ django-admin runserver

Starts nav, on port 8000.

Troubleshooting
===============

1. cannot access the database
-----------------------------

This is usually caused by the environment not having been set correctly.

Check if the the file ``sitecustomize.py`` exists in the distro-installed
Pythons (Ubuntu does this). This overrides the ``sitecustomize.py`` that is
created by ``make local-setup``.

You can either remove the global ``sitecustomize.py`` or set the environment
variables some other way, see
``.venv/lib/python*/site-packages/sitecustomize.py`` for wthat variables to
set.
