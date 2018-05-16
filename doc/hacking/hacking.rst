=====================
Hacker's guide to NAV
=====================

If you are contributing code to Network Administration Visualized,
please read this first.



Contributing to NAV
===================

Originally, NAV was a closed source project, initiated by the
Norwegian University of Science and Technology (NTNU), and eventually
sponsored by Uninett on behalf of the Norwegian higher education
community.  In 2004, however, NTNU and Uninett started distributing
NAV under the GNU General Public License, making it a truly free
software system.

While Uninett and NTNU are still the main contributors to NAV,
developing NAV to support the needs of the Norwegian higher education
community, contributions from third parties is highly appreciated.

We communicate mainly through mailing lists, GitHub_, and the ``#nav`` IRC
channel on *FreeNode*. At times, Uninett also arranges workshops and
gatherings for its customers: Norwegian universities, university colleges and
research institutions.

To contribute:

Go to https://nav.uninett.no/ and

* Join the mailing lists.  The ``nav-dev`` mailing list in
  particular is for discussing NAV development.  So far, this is a
  low traffic list. We can only hope this will change ;-)
* Get a copy of the latest development sources by cloning the
  Git-repository at GitHub_.
* Take a look at the `project reports from previous development projects at
  NTNU <https://nav.uninett.no/wiki/navprojects>`_ (NAVMe, NAVMore, tigaNAV
  and others) - design specifications and other useful bits of historic NAV
  information is mostly to be found in these. Unfortunately, some of the
  oldest project documentation is in Norwegian only. Do not hesitate to ask
  for help on the mailing lists.

If you wish to contribute code to the project, see the
:ref:`submitting_patches` section.

Directory layout
================

A rough guide to the source tree:

===========  =================================================================
Directory    Description
===========  =================================================================
bin/         NAV 'binaries'; executable scripts and programs.
contrib/     User contributed NAV tools. NAV doesn't depend on these, and any
             maintenance of them is left up to the original developers. We do
             not offer support for these tools.
doc/         User and developer documentation.
etc/         Example/initial configuration files.
htdocs/      Static media such as CSS stylesheets, images and JavaScript to be
             served by a webserver.
packages/    Stuff to help packaging NAV for various platforms, such as
             RedHat, CentOS, FreeBSD, Debian and soforth. **Much of this is
             outdated today.**
python/      Python source code.
sql/         SQL schema definitions and installation/sync tools.
templates/   Django HTML templates.
tests/       Automated tests.
tools/       Scripts for aiding in various development, build and release
             processes.
===========  =================================================================


Development languages and frameworks
====================================

All NAV back-end code is written in **Python**. The web-based user
interface is implemented using the Python-based **Django** framework. *In
addition, there is an increasing amount of **Javascript** in the web-based
user interface.

If you wish to contribute something really useful that doesn't use Python,
we may consider including it in the :file:`contrib/` directory.


Coding style
============

NAV code adheres to the Python style guide documented in :pep:`8`.
Conventions for writing good documentation strings (a.k.a. "docstrings")
are immortalized in :pep:`257`.

Much of the legacy NAV code was, however, written without using any
specific guidelines for coding style. We are working to improve this, and
will accept patches that clean existing code.


Python boilerplate headers
--------------------------

We will generally only accept code into NAV if it is licensed under
GPL v2, but we may make individual exceptions for code licensed under
compatible licenses.  Each Python source code file should contain the
following boilerplate at the top::

    #
    # Copyright (C) 2008,2009 Somebody
    #
    # This file is part of Network Administration Visualized (NAV).
    #
    # NAV is free software: you can redistribute it and/or modify it under the
    # terms of the GNU General Public License version 2 as published by the Free
    # Software Foundation.
    #
    # This program is distributed in the hope that it will be useful, but WITHOUT
    # ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
    # FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
    # more details.  You should have received a copy of the GNU General Public
    # License along with NAV. If not, see <http://www.gnu.org/licenses/>.
    #

If a file uses non-ASCII characters, it **must** be encoded as *UTF-8*, and an
encoding statement should be inserted at the top::

    # -*- coding: utf-8 -*-

Javascript
----------

When writing Javascript code, try to focus on modules, not pages. If the
code is HTML-related, it should take selectors or objects as input and
concern itself solely about those. This makes for much easier testing and
reuse. And of course - write the tests first.

When the module is done you write a controller for the page that plugs the
needed plugins to the page elements. This should fail gracefully if the
needed elements are not present.

NAV's Javascript uses RequireJS_ - use this to create modules and specify
dependencies.

Pro tip is to create :file:`require_config.dev.js` in :file:`htdocs/js/``
and add the following configuration to RequireJS:

.. code-block:: javascript

   require.urlArgs = "bust=" +  (new Date()).getTime();

This makes sure your not using cached resources in your browser when
developing, something browsers love to do! See `config-urlArgs
<http://requirejs.org/docs/api.html#config-urlArgs>`_ in the RequireJS
documentation for details. :file:`require_config.dev.js` is listed in the
repository :file:`.gitignore` file.



Database
========

NAV uses PostgreSQL as its database backend.  Namespaces (schemas) are
employed to logically group tables and relations.  NAV versions prior
to 3.5 employed separate PostgreSQL databases instead of namespaces.

The namespaces currently in use are:

=========  ===================================================================
Namespace  Description
=========  ===================================================================
manage     The core knowledge database of NAV, containing all sorts of
           information about the monitored IP Devices, events, alerts,
           network topology and machine tracking data.
profiles   Contains NAV user accounts and groups, user preferences and alert
           profiles.
logger     Anything related to NAV's syslog parser/browser system.
arnold     The port detention system Arnold stores it's data here.
radius     Radius accounting logs, updated directly by FreeRadius' PostgreSQL
           module.
=========  ===================================================================


Connecting to the database (Python)
-----------------------------------

Raw SQL
~~~~~~~

To obtain a connection to the NAV database, use the API accordingly,
e.g.::

    import nav.db
    # Get a connection to the NAV database
    connection = nav.db.getConnection('default')

The above code will open a connection to NAV's database, or, if a
previous connection with these parameters is already open, returns the
already existing connection from a connection cache.

The ``default`` parameter is there for legacy reasons; it specifies the
name of a subsystem. The :file:`db.conf` file allows configuration of
separate database users for each subsystem (known as a *script* in
:file:`db.conf`) of NAV. The default :file:`db.conf` file specifies a
database user for a subsystem called ``default``, and also specifies the
same database user for all known subsystem names. At present, using a
subsystem name that is not configured in :file:`db.conf` will cause
``nav.db.getConnection()`` to revert to using the ``default`` name.

Django models
~~~~~~~~~~~~~

NAV 3.5 and on includes Django models for most database tables.  If no
SQL magic is needed to perform your database voodoo, it is recommended
that you use these models, located in the module ''nav.models''.  You
do not need to explicitly establish a database connection to use these
models, as Django takes care of all that.

The models are defined in modules of the ''nav.models'' package.

Changing the schema
-------------------

The baseline schema is located in :file:`sql/baseline/` - the
:program:`navsyncdb` program is responsible for running this when creating
a new database. To make a schema change, you **do not** change the
baseline, but go to the :file:`sql/changes/` directory and create a new
schema change script there.

Schema change scripts as numbered, using the following pattern::

    sc.<major>.<minor>.<point>.sql

The ``<major>`` and ``<minor>`` numbers usually correspond to the major and
minor number of the next NAV release. The ``<point>`` number is a sequence
id - pick the next free number when creating a schema change script.

Remember these points when creating a schema change script:

* Create separate change scripts for unrelated schema changes.
* Remember to write SQL to **migrate** existing data, if necessary.
* Do not use transactional statements - :program:`navsyncdb` will take care
  of that.

To apply your change scripts, just run :program:`navsyncdb`. It will look
inside the ``schema_change_log`` table to see which change scripts have
already been applied, and it will detect your new change script and apply
this to the database.

.. NOTE:: When changing the schema, don't forget to update the Django
          models in the :py:mod:`nav.models` package. An integration
          test exists to verify that the Django models can at least be used
          to run proper SELECT statements against the database.


Version Control
===============

NAV uses Git_ for distributed version control. The official repository
is located at GitHub_ . Fork that and submit pull-requests for review.


Push access
-----------

Push access to the official repositories is limited to developers
employed or commissioned by Uninett.

Testing and Continuous Integration
==================================

Much of NAV is **legacy code**, as defined by *Michael C. Feathers*:
"Code that has no tests".  We have been making an effort to introduce
automated tests into the codebase the past several years, and hope
to improve coverage over time.

All test suites (except those for Javascript) are located in the
:file:`tests/` subdirectory.

Running tests
-------------

We use pytest_ to run the test suite. A bundled version is included as
:file:`runtests.py` in the :file:`python/` subdirectory, and is used to run
the unit tests only when a :kbd:`make check` command is issued in the
:file:`python/` subdirectory.

There's also a script to produce an entire test environment as a Docker
image and to run the entire test suite inside a Docker container created
from that image. This is actually the same method employed by our Jenkins
build servers to run the test suite. Take a look in the
:file:`tests/docker/` directory.


Javascript testing
------------------

Testing javascript in NAV is straightforward. We use Karma_ as a testrunner,
Mocha_ as testing framework and Chai_ as assertion library.

.. code-block:: sh

   cd htdocs/static/js

   # Install required libs, you need npm installed
   npm install

   # Run tests. This will start browsers. Karma will make sure that tests will
   # run on changes in js-files.
   ./node_modules/karma/bin/karma start test/karma.conf.js

All tests are located under :file:`htdocs/statis/js/test/`. Create new tests
there. For syntax, assertions and related stuff take a look at the tests
already there and the relevant documentation linked above.



Jenkins
-------

We use Jenkins_ (formerly *Hudson*) for Continuous Integration testing of
NAV. All the automated tests are run each time new changesets are pushed to
the official NAV repositories. Jenkins also runs pylint_ to create stats on
code quality.

Our Jenkins installation is available on https://ci.nav.uninett.no/ .

Tips and tricks
===============

Make fixtures for integration testing
-------------------------------------

.. code-block:: python

   from django.core import serializers
   from nav.models.manage import Netbox

   fixtures = serializers.serialize("xml", Netbox.objects.all()[:2])

Fixtures can so be used in your integration tests by extending
the test case DjangoTransactionTestCase in :py:mod:`nav.tests.cases`.

See :py:mod:`nav.tests.integration.l2trace_test` for an example on applying
fixtures for your particular test case.

See https://docs.djangoproject.com/en/1.7/topics/serialization/

.. TODO:: Be able to use `django-admin's management command: dumpdata
   <https://docs.djangoproject.com/en/dev/ref/django-admin/#dumpdata-appname-appname-appname-model>`_
   to create fixtures.


.. _submitting_patches:

Submitting patches
==================

Unless you are submitting one-off fixes for bugs and small issues,
please take the time to discuss your change proposals on the
**nav-dev** mailing list.  This will increase the chances of having
your patches accepted.

Base your patches on the relevant Git branches. If you are submitting
a patch for an issue that affects the latest stable series, base your patch
on that series branch (``<major>.<minor>.x``). If you are submitting
patches containing new features, base them on the ``master`` branch.

The **best way** to submit your patches is to use GitHub_: Fork our repository there
and create a pull request for us to review.

Another option for a simple patch is to attach it to a GitHub_ issue report.


.. _GitHub: https://github.com/UNINETT/nav
.. _RequireJS: http://requirejs.org/
.. _Git: https://git-scm.com/
.. _pytest: http://pytest.org/
.. _Buster.JS: http://busterjs.org/
.. _the Buster documentation: http://docs.busterjs.org/en/latest/#user-s-guide
.. _Node.js: http://nodejs.org/
.. _Jenkins: http://jenkins-ci.org/
.. _pylint: http://www.pylint.org/
.. _Karma: https://github.com/karma-runner/karma-mocha
.. _Mocha: http://mochajs.org/
.. _Chai: http://chaijs.com/
