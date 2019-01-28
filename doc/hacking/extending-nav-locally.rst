=======================
 Extending NAV locally
=======================

NAV provides some simple ways to hook into its behavior, without modifying NAV
code, by manipulating which Python modules are loaded, or manipulating Django
settings and templates.

.. note:: Some of the paths provided here will refer to ``${configdir}``. This
          is the NAV configuration directory, as output by the ``nav config
          where`` command.

Python search path modifications
--------------------------------

NAV adds ``${configdir}/python`` to Python's search path. This means that the
Python interpreter that executes NAV processes will also be able to load any
Python module from :file:`${configdir}/python/`.

Django local site settings
--------------------------

NAV's Django site settings file sits in the NAV package hierarchy,
:py:mod:`nav.django.settings`. However, this module will use `Rob Golding's
method <https://code.djangoproject.com/wiki/SplitSettings#RobGoldingsmethod>`_
in an attempt to load local site settings from a ``local_settings`` module.

By exploiting the abovementioned search path modification, you could add your
amazing homegrown ``my.amazing.app`` to the NAV web interface by adding a
``local_settings`` module thus:

.. code-block:: python
   :caption: ${configdir}/python/local_settings.py

   LOCAL_SETTINGS = True
   from nav.django.settings import *

   INSTALLED_APPS += (
       'my.amazing.app',
   )

Just remember that NAV does not use Django's migrations framework to define its
SQL schemas, so you'll have to do the legwork here yourself.

Overriding Django templates
---------------------------

NAV adds ``${configdir}/templates`` to its Django template search path. You can
override NAV's existing Django templates by placing your own in this
directory - although we wouldn't recommend it, as it can easily break your
existing NAV site on upgrades.


See :doc:`web-interface-customization` for information on more integrated ways
to hook into NAV.

