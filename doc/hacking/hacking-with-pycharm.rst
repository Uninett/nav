====================
Hacking with PyCharm
====================

`JetBrains PyCharm <http://www.jetbrains.com/pycharm/>`_ is a Python IDE with
a complete set of tools for productive development with the Python programming
language. In addition, the IDE provides high-class capabilities for
professional Web development with Django framework.

JetBrains has kindly issued an open source license to the NAV development
project.

Obtaining a copy of the open source license
-------------------------------------------

Active NAV developers may be eligible to receive a copy of the open source
license. The license must be renewed annually. Contact nav-support@uninett.no
for inquiries.

Configuring PyCharm for use with NAV
------------------------------------

Here are some tips for configuring PyCharm for efficient NAV development.

Running unit tests automagically on code changes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Click :menuselection:`Run --> Edit Configurations`:

* Click the **+** sign on the top left of the dialog to add a new run
  configuration.
* Select :menuselection:`Python tests --> py.test` in the appearing menu.

Run configuration options should be the following:

:Name: NAV UNIT TESTS
:Target: :file:`tests/unittests`
:Python interpreter: Select the correct interpreter for your project.
:Working directory: Set this to the root of your checked out source code.

If you are developing using Vagrant or Docker, make sure to select a *remote Python
interpreter* on your virtual box, otherwise make sure you have all NAV
dependencies available to your selected interpreter.

Click :guilabel:`Ok` to save your changes.

Generate documentation
^^^^^^^^^^^^^^^^^^^^^^

Click :menuselection:`Run --> Edit Configurations`:

* Click the **+** sign on the top left of the dialog to add a new run
  configuration.
* Select :menuselection:`Python docs --> Sphinx task` in the appearing menu.

Run configuration options should be the following:

:Name: Build NAV Sphinx docs
:Command: html
:input: :file:`doc`
:output: :file:`doc/html`
:Project interpreter: Select the correct interpreter for your project.
:Working directory: Set this to the root of your checked out source code.

Click :guilabel:`Ok` to save your changes. After run the new Sphinx task, you
should be able to access the documentation under :file:`doc/html` in your
checkout.

Karma integration
^^^^^^^^^^^^^^^^^

.. NOTE:: The Karma plugin is only available under PyCharm 3.0 and later.

Select :menuselection:`File --> Settings` from the menu. Go to
:guilabel:`Plugins` under :guilabel:`IDE Settings` and click the
:guilabel:`Install Jetbrains plugin` button.

Select and install the *Karma* plugin from the list. A restart of the IDE
might be necessary.

Click :menuselection:`Run --> Edit Configurations`:

* Click the **+** sign on the top left of the dialog to add a new run
  configuration.
* Select :menuselection:`Karma` in the appearing menu.

Run configuration options should be the following:

:Node.js interpreter: should point to wherever your :program:`node` binary is
                      installed.
:Karma Node.js package: :file:`python/nav/web/static/js/node_modules/karma`
:Configuration file: :file:`python/nav/web/static/js/test/karma.conf.js`

Now you should be able to run both tests and tests with coverage.
