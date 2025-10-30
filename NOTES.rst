=================================================
 Network Administration Visualized release notes
=================================================

Please report bugs at https://github.com/uninett/nav/issues/new/choose . To browse
existing bug reports, go to https://github.com/uninett/nav/issues .

To see an overview of upcoming release milestones and the issues they resolve,
please go to https://github.com/uninett/nav/milestones .

NAV 5.15
========

Dependency changes
------------------

Python modules with changed version requirements:

* :mod:`napalm` (``>=5.1.0,<5.2.0``)


Shareable dashboards
--------------------

Users can now elect to share their dashboards with other users of the same NAV
installation. Instead of relying on exporting a static dashboard definition to
JSON and having other users import this definition, users can now *subscribe*
to other users' shared dashboards.

The active dashboard can be marked as shared by opening the dashboard
configuration dialog (the cog icon on the right-hand side of the screen) and
click on "Share dashboard", followed by clicking on the "Save sharing settings"
button.

Discovering the shared dashboards of other users is done by clicking the "add
dashboard" button (the plus sign next to your dashboard list) and then clicking
on "Find shared dashboard". Search for a dashboard name or another user's
name. Clicking on a shared dashboard name gives you a preview of the dashboard.
To keep it permanently in your list of dashboards, you must click on the
"Subscribe" button.

When viewing a dashboard, its owner is clearly named in top right corner of the
dashboard.


NAV 5.14
========

Dependency changes
------------------

Python modules with changed version requirements:

* :mod:`djangorestframework` (``>=3.14``)
* :mod:`napalm` (``>=5.0.0,<5.1.0``)
* :mod:`twisted` (``>=24.7``)

These Python modules are new requirements:

* :mod:`django-htmx`


IP Device Info refresh
----------------------

Each IP Device's *IP Device Info* page shows an ipdevpoll job status list in
the lower right corner. This NAV release finally adds the much-discussed
**Refresh** button to these entries.

The **Refresh** button will ask the :doc:`/reference/ipdevpoll` background
process to schedule the selected job for an immediate re-run. Once the refresh
is complete, the entire page will reload to show the potentially updated
information.


Issuing API JSON Web tokens (JWT)
---------------------------------

Since version 5.11, NAV has provided simple support for authorizing access to
the API using JSON Web Token signed by authorized third parties.  This release
adds two new, important features to complement this:

* Signed JWTs can now include claims about read/write-level access and which
  API endpoints it should be authorized to access
* NAV can now issue its own JSON Web Tokens, through the *User and API
  Administration* tool.

More information about creating the necessary keys and configuring NAV to issue
JWTs can be found in :ref:`local-jwt-configuration`.

We expect to deprecate and remove the old opaque token system in future
releases, once JWT support stabilizes.


QR code generation
------------------

This release adds two new QR code generation features:

* A new item ``QR Code`` has been added to the ``My stuff`` dropdown menu
  present on every NAV page. Clicking this will generate and display a QR code
  "bookmark" that links back to the URL you are currently viewing.
* The *Seed Database* IP Device listing tab now has a button to generate a ZIP
  file archive of QR codes linking back to the selected devices. This can
  potentially be used to print a bunch of QR codes to glue to your equipment,
  so they can be easily scanned and found in NAV while on-site.


New API endpoints
-----------------

Two new API endpoints have been added:

* ``/api/1/netboxentity/`` can be used to list the internal physical entities
  that NAV has detected in your devices (chassis, modules, ports, fans, PSUs,
  etc.), as well as their serial numbers.
* ``/api/1/vendor/`` can be used to perform bulk OUI vendor lookups for MAC
  addresses, based on NAV's downloaded IEEE OUI registry.


Insecure password warnings
--------------------------

The *User and API administration* tool account list has for several years
included warnings about users with potential password problems. One of the
typical problems are passwords that were last changed in very old versions of
NAV, which would use password hashing schemes that would no longer be
considered secure today.

These warnings seem to be too unobtrusive for administrators to notice;
therefore, this NAV release will display a warning banner to all admins on all
NAV pages that there are users with potential password problems. The individual
users that have these password problems will also be shown a similar banner
about their own account.

"Quickselect" form in *Maintenance* and *Device history* tools has been replaced
--------------------------------------------------------------------------------

The so-called "quickselect" form, used to find and select components for adding
to maintenance tasks, or to search for device history of selected components,
was built using ancient Javascript technology about 18 years ago.  It had
several issues and was really slow on NAV installations with many IP Devices,
rooms or locations.

The form has been entirely replaced by a more dynamic search tool, which will
dynamically search the NAV database for matching components as you type into
the search bar.


Collecting DHCP pool statistics from KEA DHCP servers
-----------------------------------------------------

This release adds a new program (and cronjob) to collect DHCP pool
usage/utilization stats from a KEA DHCP server API (:program:`navdhcpstats`)
every five minutes and store these as time series data in NAV's associated
Graphite server.  This program is intended to be extensible, so that
implementations for other APIs can be added as plugins.

We are working on graphing these statistics in the *Prefix* and *Vlan* detail
pages in the NAV web UI, and expect to include this feature in the next
release.  Until then, the only documentation for this new command is in the
comments of its configuration file, :file:`dhcpstats.conf`.


NAV 5.13
========

Dependency changes
------------------

NAV 5.13 will run properly on Python 3.11.

Dependencies to these Python modules have been added:

:mod:`pytz`

Python modules with changed version requirements:

* :mod:`Django` (``>=4.2,<4.3``)
* :mod:`djangorestframework` (``>=3.12`` - in practice, 3.15 at the time of release)
* :mod:`napalm` (``>=5.0.0,<5.1.0``)

OUI lookup in Machine Tracker searches
--------------------------------------

The first three octets of a MAC hardware address is considered its OUI
(Organizationally Unique Identifier), and identifies a vendor, manufacturer or
other organization (as assigned by the IEEE).

NAV 5.11 added the :program:`navoui` program to fetch OUI assignments from IEEE
and populate the NAV database with them.  NAV 5.13 finally utilizes this
information by adding optional vendor lookups to Machine Tracker searches.

A new cron job, ``navoui``, is also added, to update the list of assignments
daily.  You will not benefit from vendor lookups in Machine Tracker until
:program:`navoui` has been run at least once. If you don't want to wait for the
first run, you can simply run the program manually.


NAV 5.12
========

Dependency changes
------------------

These Python modules are no longer required:

* :mod:`django-crispy-forms`
* :mod:`crispy-forms-foundation`
* :mod:`libsass`

If you want to build NAV from source, you will now need `webpack
<https://webpack.js.org/>` as a replacement for the now defunct :mod:`libsass`.
Webpack is used to build many of the static resources (mostly CSS stylesheets
from SASS source files) that are to be served by the NAV web GUI.

Deprecation warnings
--------------------
.. warning:: The ``[paloaltoarp]`` section of :file:`ipdevpoll.conf`, used for
             configuring HTTP-based ARP fetching from Palo Alto firewalls, is
             deprecated and will be ignored in NAV 5.12 and future versions.
             HTTP-based ARP fetching from Palo Alto
             firewalls *must* now be configured using management profiles,
             analogous to configuration of SNMP-based fetching.  :ref:`See below
             for more details<5.12-new-http-rest-api-management-profile-type>`.

Change ``ip2mac`` plugin order in :file:`ipdevpoll.conf`
--------------------------------------------------------

The Palo Alto ARP plugin in ipdevpoll had a problem which caused the ARP
records it collected from Palo Palo firewalls to be unduly closed by the
regular SNMP-based ARP plugin.  This release of NAV fixes this by making the
SNMP-based ARP plugin a "fallback" mechanism that doesn't touch ARP collection
if another plugin has already collected ARP data.

In order for this fix to work, **you must change the order of the plugins** in the
``[job_ip2mac]`` section of your :file:`ipdevpoll.conf` file, to ensure that
the ``paloaltoarp`` plugin is listed *before* the ``arp`` plugin.


.. _5.12-new-http-rest-api-management-profile-type:

New way to configure fetching of Palo Alto firewall ARP cache data
------------------------------------------------------------------
.. NOTE:: See
          :ref:`management profile reference documentation<http-rest-api-management-profile>`
          for instructions on how to reconfigure your Palo Alto firewall
          devices in NAV 5.12 to enable support for fetching of their
          ARP information.

Starting with NAV 5.12, a new ``HTTP API`` management profile type has been
added to NAV for configuring HTTP API specific parameters used in fetching of
ARP information from Palo Alto firewalls running PAN-OS. Currently, this
management profile type is only used to configure Palo Alto firewall devices. If
support for other devices that similarly can be managed using a HTTP API is
added to NAV in future releases, you can expect to be able to configure API
parameters for these devices by using management profiles as well.


NAV 5.11
========

This is mostly an interim release to shed old dependencies that are ultimately
keeping NAV from running on Python 3.11 and newer.  While there are some bug
fixes, the main new user-facing feature in this release is the completion of
the lifecycle events system.

Dependency changes
------------------

.. IMPORTANT:: NAV 5.11 requires PostgreSQL to be at least version *13*.
.. IMPORTANT:: NAV 5.11 no longer supports Python versions older than *3.9*.

Python modules with changed version requirements:

* :mod:`twisted` (``>=23.8.0<24.0``)
* :mod:`sphinx` (``==7.4.7``)

New Python modules required:

* :mod:`requests`
* :mod:`pyjwt` (``>=2.6.0``)

These Python modules are no longer required due to support for Python versions
older than 3.9 being dropped:

* :mod:`backports.zoneinfo`
* :mod:`importlib_metadata`
* :mod:`importlib_resources`


More lifecycle events
---------------------

NAV 5.11 adds more lifecycle events that are posted when devices disappear or
are removed (i.e. they appear to be taken out of service and put on the shelf),
enabling a more complete lifecycle log of individual devices:

* ``deviceDeletedFan`` is posted for fan entities that disappear from IP devices.
* ``deviceDeletedPsu`` is posted for power supply entities that disappear from IP devices.
* ``deviceDeletedChassis`` is posted for a chassis that are forcibly deleted
  from a stack by a NAV operator (using the status or device history tools).
* ``deviceDeletedModule`` is posted for a module that are forcibly deleted from
  an IP device by a NAV operator (using the status or device history tools).

Features in the making
----------------------

The changelog references several features that are not yet complete, that will
be completed in upcoming feature releases.  These include:

* Replacing the existing opaque API token system with self-signed JSON Web
  Tokens (JWTs).  NAV already supports API authentication through JWTs signed
  by authorized third parties.

* An OUI vendor database is added to NAV, in order to keep track of which MAC
  address prefixes are assigned to which hardware vendors.  This will be
  utilized for machine tracker searches in a future NAV release.


NAV 5.10 (Unreleased)
=====================

Deprecation warnings
--------------------

.. warning:: The next feature release of NAV (5.11) will drop support for
             Python versions older than 3.9.

Dependency changes
------------------

.. IMPORTANT:: NAV 5.10 requires PostgreSQL to be at least version *11*.

New dependencies
~~~~~~~~~~~~~~~~

Dependencies to these Python modules have been added in order to support
communicating with Palo Alto firewall APIs:

* :mod:`PyOpenSSL` (``==23.3.0``)
* :mod:`service-identity` (``==21.1.0``)

Support for fetching ARP cache data from Palo Alto firewalls
------------------------------------------------------------

Palo Alto firewalls do support SNMP.  They do not, however, support fetching
ARP cache data using SNMP.  A new ipdevpoll plugin, ``paloaltoarp``, has been
added to fetch ARP cache data using the REST API built in to these firewall
products.

Access credentials for Palo Alto firewalls need to be configured in
:file:`ipdevpoll.conf`, but a later NAV release should move to providing
management profiles also for this.

Please read more in :doc:`the ipdevpoll reference documentation
</reference/ipdevpoll>` for configuration details.

Changed names of NAV command line programs
------------------------------------------

NAV 5.9 changed the names of most of NAV's command line programs by removing
their ``.py`` file name extensions.  However, the :program:`snmptrapd` program
had a naming conflict with Net-SNMP's trap daemon, if installed.  NAV 5.10.1
renames the NAV trap daemon to :program:`navtrapd`.  Please ensure your
:file:`daemons.yml` configuration file is up to date after an upgrade.


NAV 5.9
=======

Changed names of NAV command line programs
------------------------------------------
NAV has switched to a more canonical way of installing Python command line
scripts, or "binaries".  This means that all NAV command line programs that
previously ended with a ``.py`` extension now have been stripped of that
extension.  Any custom cron jobs or scripts you have that may reference these
NAV commands must be updated in order to continue working.

It also means that you need to make sure your :file:`daemons.yml` configuration
file is up-to-date after an upgrade, as well as the NAV cronjob snippets in the
:file:`cron.d/` configuration directory.

These commands are affected and no longer have a ``.py`` extension:

* ``alertengine``
* ``autoenable``
* ``collect_active_ip``
* ``emailreports``
* ``logengine``
* ``macwatch``
* ``mailin``
* ``maintengine``
* ``netbiostracker``
* ``pping``
* ``radiusparser``
* ``servicemon``
* ``smsd``
* ``snmptrapd``
* ``sortedstats_cacher``
* ``start_arnold``
* ``t1000``

Web security
------------

While it is only relevant for older browsers, the HTTP header
``X-XSS-Protection`` is set to ``1; mode=block``. It does not affect browsers
that do not support it after all.

There's a new section in :file:`webfront/webfront.conf`, ``[security]``. When
running in production with SSL/TLS turned on, there's a new flag ``needs_tls``
that should also be toggled on. This'll turn on secure cookies (only sent over
SSL/TLS). See also the new howto
:doc:`Securing NAV in production </howto/securing-nav-in-production>`.

NAV 5.8
=======

Dependency changes
------------------

Upgrade your :mod:`pynetsnmp-2` library to at least version *0.1.10* to ensure
SNMPv3 compatibility.

SNMPv3
------

NAV 5.8 finally adds SNMPv3 support, although it is not yet 100%
feature-complete.  A new management profile type has been added specifically
for SNMPv3.  SNMPv3 management requires a host of configuration attributes,
whereas v1/v2c only requires a community string.

Additionally, if a device only has write-enabled SNMP management profiles
attached to it, NAV will now try to use those also for read operations.  If
your SNMPv3 profile supports both reading and writing, you should be able to
get by with a single profile per device.


Missing SNMPv3 features
~~~~~~~~~~~~~~~~~~~~~~~

**SNMPv3 traps**

SNMPv3 trap support is still being worked on, but no working solution is
available in 5.8.  See `issue #2755 for snmptrapd implementation and progress
details <https://github.com/Uninett/nav/issues/2755>`.

**SNMPv3 contexts**

Various vendors use the concept of "community indexing" to fetch multiple
logical instances of MIBs.  Examples include Cisco switches, where multiple
instances of the ``BRIDGE-MIB`` are kept, one for each active VLAN.  To access
the switch forwarding tables of VLAN 12 with an SNMP community of ``public``,
the community must be modified to ``public@12``.

Another common example is devices that allow SNMP management of individual VRF
instances by modifying the SNMP community.

However, since SNMPv3 does not use community strings, it instead provides the
concept of "contexts", where the default context is typical an empty string.

:program:`ipdevpoll` does not yet support using SNMPv3 contexts as a
replacement for community indexing, so the types of data described above may be
missing from some devices if switching them to SNMPv3.


Power-over-Ethernet configuration in PortAdmin
----------------------------------------------

PortAdmin has gained supported for enabling/disabling Power-over-Ethernet on
Juniper and Cisco switches.  The available configuration options will vary from
device to device and vendor to vendor, so the available presets will simply be
presented for selection in a dropdown menu if PoE support is detected on a
device.

REMOTE_USER autocreate option
-----------------------------

The external authentication integration system (popularly named
``REMOTE_USER``) has gained a new toggle ``autocreate`` in the
``[remote-user]`` section of :file:`webfront/webfront.conf`.  This option is
``False`` by default, meaning that externally authenticated users will not be
allowed to use NAV unless they have already been pre-created in the user admin
panel.

This changes the old behavior, in where any unknown user referenced in the
``REMOTE_USER`` header by the web server is automatically created in NAV.  If
you need the old functionality, you need to set this option to ``True``.


NAV 5.7
=======

Dependency changes
------------------

We have removed the upper version bound requirement for the :mod:`Pillow` library.

Detection and alerting of Juniper chassis/system alarms
-------------------------------------------------------

Juniper devices have a concept of chassis and system alarms (e.g. a failing PSU
might trigger such an alert). Alarms are categorized as either *yellow* or
*red* alarms, depending on the running hardware and operating system.

Juniper provides SNMP MIBs to poll information about the current number of
alarms of each category, but does not provide for fetching information about
individual active alerts.  To get details about ongoing alarms, one usually
needs to access the device CLI to get the current status.

NAV 5.7 adds support to poll the number of *yellow* and *red* alerts from a
Juniper device, and produces its own alerts when any of these counts are
non-zero.

Two new event types are introduced, which can be used for subscriptions in
Alert Profiles:

* ``juniperYellowAlarmState``
* ``juniperRedAlarmState``


``contains_address`` filter on ``prefix`` API endpoint
-------------------------------------------------------

The ``prefix`` API endpoint has been updated to include a new
``contains_address`` filter.  This can be used to filter prefixes based on
whether they contain specific addresses.  To search for prefixes that match
single IP addresses, a host mask can be used.  E.g., to get all prefixes that
match a single host ``10.0.0.42``, query for ``10.0.0.42/32``, like
``/api/1/prefix/?contains_address=10.0.0.42%2F32``.


Even more flexible configuration of logging
-------------------------------------------

Advanced users will find that we have added more options for configuring NAV's
logging output.  The available configuration options are explored in depth
:doc:`in our new logging howto guide </howto/setting-up-logging>`.

NAV 5.6
=======

Dependency changes
------------------

New dependencies
~~~~~~~~~~~~~~~~

Dependencies to these Python modules have been added:

* :mod:`backports.zoneinfo` (only necessary when running on Python versions older than 3.9)
* Our own fork of :mod:`drf-oidc-auth`, as found at ``git+https://github.com/Uninett/drf-oidc-auth@v4.0#egg=drf-oidc-auth``


NAV 5.5
=======

Dependency changes
------------------

None :-)

API changes
-----------

The ``/netbox/`` API endpoint adds a new read-only attribute:
``mac_addresses``. This is a list of MAC addresses associated with an IP
Device's chassis, typically collected from either ``LLDP-MIB`` or
``BRIDGE-MIB``. In most cases, devices will only have a single address here,
but sometimes, the two MIBs will disagree on what is the main "chassis"
address.

The ``/interface`` endpoint has gained two new read-only attributes for LAG
information:

* ``aggregator``: An interface that is part of an aggregate will have the
  aggregate interface specified here. The aggregator will be identified by both
  its ``id`` and ``ifname`` attributes.
* ``bundled_interfaces``: An interface that aggregates multiple interfaces will
  have those interfaces listed here. Each interface in the list will be
  identified by their ``id`` and ``ifname`` attrbutes.

Software upgrade history
------------------------

NAV has finally regained the ability to save device software, firmware and/or
hardware upgrades as events to their history, as the new ``deviceSwUpgrade``,
``deviceFwUpgrade`` and ``deviceHwUpgrade`` alert types have been added to the
``deviceNotice`` event hierarchy.  These alerts can now be subscribed to in
Alert Profiles, and will be searchable in the Device History tool.  See also
:doc:`reference/alerttypes` for the full list of events/alerts NAV provides.

Juniper ``BUILTIN`` devices
---------------------------

Juniper equipment tends to report soldered-on linecards as field-replaceable
modules through their implementation of ``ENTITY-MIB::entPhysicalTable``. These
modules are also all reported as having the same serial number: ``BUILTIN``.

NAV versions prior to 5.5.1 did not safeguard against this Juniper bug. This
would cause NAV installations that monitor Juniper equipment to have a single
device with the ``BUILTIN`` serial number, which was shared between all
monitored Juniper netboxes.  The attributes of ``BUILTIN`` devices (such as
software or firmware revision) would be different across most Juniper netboxes,
causing them to compete for updates of the attributes in the NAV database.

This went under the radar until NAV 5.5.0 re-introduced the ``device*Upgrade``
set of alerts. Now, every time a Juniper netbox is polleed and the shared
``BUILTIN`` device's software/hardware/firmware revision was changed, an alert
would be generated. For those unfortunate enough to subscribe to all NAV
alerts, this would lead to a storm of alerts.

Subsequently, NAV 5.5.1 deletes this shared ``BUILTIN`` device from the
database, and adds functionality to ignore any module or entity that reports
this as its serial number.


NAV 5.4
=======

Dependency changes
------------------

Changed dependencies
~~~~~~~~~~~~~~~~~~~~

These Python modules have changed version requirements:

* :mod:`sphinx` ==4.4.0
* :mod:`pynetsnmp-2` >=0.1.8,<0.2.0
* :mod:`napalm` ==3.4.1

New dependencies
~~~~~~~~~~~~~~~~

Dependencies to these Python modules have been added:

* :mod:`sphinxcontrib-programoutput` ==0.17

Removed dependencies
~~~~~~~~~~~~~~~~~~~~

* The :mod:`six` Python module is no longer required. It was only needed under
  Python 2 to keep compatibility with both Python 2 and 3, but NAV 5.1 dropped
  support for Python 2.


NAV 5.3
=======

Changes in governance and code ownership
----------------------------------------

On January 1st 2022, Uninett, NSD and Unit (all entities owned by the Norwegian
government) were merged into the new governmental agency *Sikt - Norwegian
Agency for Shared Services in Education and Research*.

This does not change our commitment to develop and provide NAV as free and open
source software. We still have the same ownership and the same goals - we're
just doing everything under a new name.

In the coming year, references to Uninett, both in the NAV documentation, code
and related web sites will slowly change into Sikt, but for some time going
forward, there will be references to both names.  For more information about
the new organization, we refer you to https://sikt.no/en/about-sikt


Dependency changes
------------------

.. IMPORTANT:: NAV 5.3 requires PostgreSQL to be at least version *9.6*.

Furthermore, NAV 5.3 moves to Django 3.2, resulting in several changes in
version dependencies of related Python libraries. These changes are normally
taken care of for you when using ``pip`` and/or virtual environments with the
supplied :file:`requirements.txt` file:

* :mod:`Django` >=3.2,<3.3
* :mod:`django-filter` >=2
* :mod:`django-crispy-forms` >=1.8,<1.9
* :mod:`crispy-forms-foundation` >=0.7,<0.8
* :mod:`djangorestframework` >=3.12,<3.13
* :mod:`Markdown` ==3.3.6

The new Django version also removes support for Python 2, and therefore removed
the bundled copy of the :mod:`six` library that NAV utilized for compatibility
with both Python versions. Therefore, until Python 2 compatibility code has
been removed entirely from NAV, NAV now depends on:

* :mod:`six`

To ensure NAV runs properly on Python 3.9, these dependency changes have also
taken place:

* :mod:`IPy` ==1.01
* :mod:`twisted` >=20.0.0,<21
* :mod:`networkx` ==2.6.3
* :mod:`dnspython` <3.0.0,>=2.1.0

To ensure the NAV documentation is built correctly, Sphinx needs an upgrade as
well:

* :mod:`Sphinx` ==3.5.4

Backwards incompatible changes
------------------------------

Report configuration files have moved
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The report generator in previous versions of NAV read two single configuration
files from the :file:`report/` configuration directory, in the following order:

1. :file:`report.conf`
2. :file:`report.local.conf`

NAV 5.3 replaces these files with a :file:`report/report.conf.d/` style
directory. Every non-hidden file that matches the ``*.conf`` glob pattern will
be read from this directory in alphabetical order by filename.

If you have made local changes to your :file:`report/report.conf` or
:file:`report/report.local.conf` files, please move these configuration files
into the new :file:`report/report.conf.d/` directory, to ensure you can still
generate your reports as expected.

NAV 5.2
=======

Dependency changes
------------------

New dependencies
~~~~~~~~~~~~~~~~

For building the NAV documentation, the Python module
:mod:`sphinxcontrib-django` is now required (it is not required for the NAV
runtime, though).


Changed versions
~~~~~~~~~~~~~~~~

NAV 5.2 moved to a newer version of the Python module :mod:`feedparser`,
because of Python 3 issues with the old version. The new requirement is:

* :mod:`feedparser` == 6.0.8

Due to recent dependency conflicts with Napalm, NAV also changed the version
requirement for the :mod:`dnspython` module. This is the current requirement:

* :mod:`dnspython` <3.0.0,>=2.1.0


Backwards incompatible changes
------------------------------

Changed Alert severity level definitions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

While a severity value was always attached to each NAV alert, and could be used
for matching in Alert Profiles, these values have always been poorly defined
and underused. They were loosely understood to be in the range *0-100*, where
*100* was the highest severity and *0* was the lowest, but more or less every
alert ever issued by NAV was set to a severity value of 50.

NAV 5.2 changes the entire severity scale and its interpretation to be a value
in the range of **1 through 5**, where *1* is the **highest** severity and *5*
is the **lowest**. This can be roughly interpreted as:

- **5** = *Information*
- **4** = *Low*
- **3** = *Moderate*
- **2** = *High*
- **1** = *Critical*

More importantly, NAV 5.2 adds the ability for you to configure how these
values are set. Read more about this in the :ref:`event engine reference
documentation on severity levels <severity_levels>`.

Changes for developers
----------------------

NAV 5.2 requires all Python code to be formatted using Black, and introduces
Git pre-commit hooks to ensure all Python code is formatted using Black before
commits are accepted. Read all about it in :doc:`hacking/hacking`.

NAV 5.1
=======

Dependency changes
------------------

Changed versions
~~~~~~~~~~~~~~~~

NAV 5.1 moves to Django 2.2, resulting in several changes in version
dependencies of related libraries:

* :mod:`Django`>=2.2,<2.3
* :mod:`django-filter`>=2
* :mod:`django-crispy-forms`>=1.7,<1.8
* :mod:`crispy-forms-foundation`>=0.7,<0.8
* :mod:`djangorestframework`>=3.9,<3.10

Also, the Python library :mod:`Pillow` requirement has been moved to version
8.0 (In reality, NAV is compatible with all versions from 3 through 8, as only
the thumbnail API call is used, but the latest version is recommended due to
reported security vulnerabilities in the older versions).

New dependencies
~~~~~~~~~~~~~~~~

For NAPALM management profiles and Juniper support in PortAdmin, a dependency
on the NAPALM_ library has been added:

* :mod:`napalm` version 3.0

Removed dependencies
~~~~~~~~~~~~~~~~~~~~

NAV no longer requires the :mod:`configparser` or :mod:`py2-ipaddress` Python
modules. They were only needed under Python 2 to keep compatibility with both
Python 2 and 3, but NAV 5.1 drops support for Python 2, as previously
announced.

Changed configuration files
---------------------------

These configuration files changed:

* :file:`portadmin/portadmin.conf`: The option ``write_mem`` has been renamed
  to ``commit``, for the sake of a a more platform and management protocol
  agnostic view of the world.

* :file:`daemons.yml`: Daemon entries now support the config option
  ``privileged``, which defaults to ``false``. A daemon with ``privileged`` set
  to ``true`` will be run as ``root``. Only :program:`snmptrapd` and
  :program:`pping` will need to run using ``privileged: true``, as these
  daemons need to create privileged communication sockets at startup (but they
  will drop root privileges immediately after the sockets have been
  created). **This means snmptrapd and pping will not start if you keep
  the old version of this config file unchanged.**


Things to be aware of
---------------------

.. note:: NAV 5.1 fixes a bug where some NAV daemons were run as root, giving
          them an unnecessarily high privilege level (never a good
          idea™). After upgrading, you may find some of these daemons failing
          to start because their existing log files are only writeable by the
          ``root`` user. You should ensure the NAV log files are all writable
          by the user NAV runs as (``navcron``, in most cases).



New features
------------

Juniper support in PortAdmin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PortAdmin has gained the ability to configure Juniper switches. Juniper does
not support configuration through SNMP writes, so the new management profile
type NAPALM_ has been introduced, which enables PortAdmin to use Juniper
specific NETCONF and RPC calls to get and set switch port configuration.

Please read the :doc:`management profiles reference docs
</reference/management-profiles>` for more details.

.. _`NAPALM`: https://napalm.readthedocs.io/en/latest/


Device filter options for distributed monitoring with pping and ipdevpoll
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :program:`pping` and :program:`ipdevpoll` daemons have gained support for
device filtering options. Using these options can limit the set of devices a
pping or ipdevpoll instance will work with, based on your already configured
device groups.

This enables a form of distributed monitoring that wasn't previously possible:
If you have a group of devices that are only accesible from the inside of some
VLAN or secure zone, you can install NAV inside this zone and configure pping
and ipdevpoll there to only monitor the devices within that zone, while telling
other pping/ipdevpoll instances to ignore those device groups.

This can also be used for low-level and manual horizontal scaling of NAV's
monitoring functions.

The new options are documented in the daemons' example config files,
:file:`ipdevpoll.conf` and :file:`pping.conf`, respectively.


New type sync script
~~~~~~~~~~~~~~~~~~~~

:program:`navsynctypes` is a new command line program to dump the NAV IP device
type registry as a series of PostgreSQL compatible commands that will update
the type registry of another NAV installation. Missing types will be added,
while existing types will have their names and descriptions updated to reflect
the names and descriptions of the source NAV installation.

Its primary use may be for someone who operates multiple NAV installations to
easily synchronize the type registry between those installations.


NAV 5.0
=======

Dependency changes
------------------

.. warning:: `Python 2 reaches its end-of-life`_ on **January 1, 2020**. NAV
             5.0 therefore moves to Python 3, and as such, you will need at
             least Python 3.5 to run NAV.

	     Most of NAV will still run on Python 2 as of the 5.0 release, but
             from this point, Python 2 will be deprecated and we will start
             removing code that exists solely to keep compatibility with
             Python 2.

.. _Python 2 reaches its end-of-life: https://www.python.org/doc/sunset-python-2/

* :mod:`xmpppy` is no longer needed.

Upgraded dependencies
~~~~~~~~~~~~~~~~~~~~~

The version requirements have changed for these dependencies:

* :mod:`Django` must be any version from the *1.11* series.
* :mod:`feedparser` must be any version from the *5.2* series.
* :mod:`networkx` must be any version from the *2.2* series.
* :mod:`IPy` must be at least version *1.00*.
* :mod:`pynetsnmp-2` must be version *0.1.5*.
* :mod:`psycopg2` must be version *2.8.4*.

Removed features
----------------

The ability to send Jabber notifications has been removed from the alert
profiles system, due to lack of demand and the no-longer maintained
:mod:`xmpppy` library.

Backwards incompatible changes
------------------------------

Daemon startup privileges
~~~~~~~~~~~~~~~~~~~~~~~~~

By accident, some of NAV's daemons have been running as the privileged ``root``
user since NAV 4.9.0, due to changes in the process control system.  NAV 5.0.4
introduces the ``privileged`` option in the :file:`daemons.yml` configuration
file, to signal which daemons actually need to be started with root privileges.

Only :program:`snmptrapd` and :program:`pping` need root privileges on startup,
as these daemons create privileged communication sockets, but they will drop
root privileges immediately after these sockets are created.

Please ensure your :file:`daemon.yml` configuration file is updated. Also, be
aware that after upgrading to NAV 5.0.4 from any version from 4.9.0 and up, you
may have some NAV log files that are owned by ``root``, which will cause some
of the daemons to fail on startup. Please ensure all NAV log files are writable
for the user defined as ``NAV_USER`` in :file:`nav.conf`.


New features
------------

Management profiles
~~~~~~~~~~~~~~~~~~~

NAV 5.0 introduces the concept of **management profiles** to facilitate future
support for *other management protocols than SNMP*. This means that individual
devices are no longer configured with read-only and read-write communities
directly on their SeedDB entries. Instead, you will need to create one or more
management profiles (also in SeedDB), that you assign to each device.

Each profile configures the options needed to communicate with a device using a
specific management protocol, such as SNMP.  If all your devices use SNMP v2c
with a read community of ``public``, you will only need a single profile, and
can assign this to all your devices (you will need another profile for
read-write access, if applicable). Conversely, if you change the community of
all your devices, you only need to change the single profile.

When upgrading from previous NAV versions, all the pre-existing and distinct
read-only and read-write communities configured on your IP devices will be
automatically converted into management profiles and assigned to those devices
that match.

The API has been updated to include an endpoint for management profiles, and
the ``netbox`` endpoint can be used to manipulate the set of profiles assigned
to an IP device.

See the updated :doc:`Getting Started Guide </intro/getting-started>` for a
simple introduction to adding a management profile.

Status monitoring of power supplies and fans on Juniper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Power supply and fan units on Juniper devices are now discovered and monitored
using the proprietary ``JUNIPER-MIB``.

Support for Alcatel DDM sensors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

DDM values collected from ALCATEL-IND1-PORT-MIB are now available as
sensors. This includes temperature, bias current, transmit output power and
receive optical power values.

The implementation was contributed by Pär Stolpe of Linköping University, and
has been specifically tested on Alcatel Lucent Enterprise OmniSwitch AOS 8.

psuwatch ipdevpoll plugin replaces powersupplywatch program
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :program:`powersupplywatch` program (run periodically in the ``psuwatch``
cronjob) has been replaced by the new ``psuwatch`` plugin, as part of the
:program:`ipdevpoll` ``statuscheck`` job. Please ensure your
:file:`ipdevpoll.conf` is properly updated.

Support for Coriant Groove devices
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

NAV now supports collecting various optic measurements (as sensors) from
Coriant Groove devices, using ``CORIANT-GROOVE-MIB``. These devices are used
for disaggregation of DWDM systems. These sensors are registered and polled:

* Optical channels

  * Frequency
  * Power
  * Differential group delay
  * Chromatic dispersion
  * S/N ratio
  * Q-factor
  * PreFEC bit error ratio

* Client ports

  * TX/RX optical power
  * TX/RX lane optical power

* ODU

  * Signal delay

Option to enable CDP on Cisco Voice VLAN ports
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PortAdmin can now explicitly enable/disable CDP on ports when
configuring/de-configuring Cisco Voice VLANs on them, if instructed to do so by
the new ``cisco_voice_cdp`` option in :file:`portadmin.conf`.

External authentication through the REMOTE_USER header
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

NAV now supports external authentication by honoring the `REMOTE_USER` HTTP
header / environment variable. See the :doc:`reference documentation for
external web authentication </reference/web_authentication>` for details.

Exporting a continuous stream of NAV alerts to third party software
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :program:`Event Engine` has gained support for starting an external program
and feeding it a continuous stream of JSON-formatted descriptions of every
alert it generates. This can be used to aggregate alerts into third party
software. More details are available in the :doc:`Event Engine reference guide
</reference/eventengine>`.


NAV 4.9
=======

License changes
---------------

With the 4.9 release, NAV moves from a **GPL v2-only** license to a **GPL v3**
license. This is strictly to remain compatible with the free licenses of third
party libraries we wish to utilize in future releases (in particular, *Apache
2.0-licensed* libraries).

NAV used to have multiple copyright owners, mainly all from the higher
education sector of Norway. Uninett was able to negotiate the transfer of these
rights before initiating a license switch. To avoid similar issues in the
future, if the need to relicense should arise again, we have adopted a
contributor license agreement.

Contributor License Agreement
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Uninett has adopted the Free Software Foundation's `Fiduciary License Agreement
(FLA) <https://fsfe.org/activities/ftf/fla.en.html>`_ for NAV. Anyone who
contributes code to NAV must sign this license before the contribution can be
accepted into NAV.

Our preferred method of receiving contributions is via GitHub pull requests.
Therefore, to reduce the overhead of the CLA signing process, we have
implemented an *digital CLA signing process* for GitHub pull requests, by the
help of `CLA assistant <https://cla-assistant.io/>`_. When submitting your
first PR against NAV, the CLA Assistant will automatically comment on the PR,
prompting you to sign the FLA digitally using your GitHub account.

We would like to stress that Uninett is a *not-for-profit*, government-owned
limited company. It is our intent to continue to keep NAV free and open for the
lifetime of the project. This is why we choose the GPL license, and this is why
we choose the FLA. The latter stipulates that our right to use your
contribution is void if we should ever attempt to relicense it to a non-open
license (ie. one that isn't approved by FSF or OSI).



Dependency changes
------------------

The NAV team is still working on porting the NAV code to Python 3, which
includes moving to more current (non-deprecated) versions of the Django
framework.  This means you will need to upgrade various dependencies when
moving to NAV 4.9.

Unfortunately, Django releases have a tendency to drop backwards compatibility
with many features, so expect future releases of NAV to move to even more
recent versions of Django - we expect to land on Django 1.11, which is the last
long-term support release of Django 1. Django 2 drops support for Python 2, as
will NAV.

NAV 4.9.4 will require this new dependency for the IPAM subnet suggest
function to work also for IPv6:

* :mod:`py2-ipaddress` must be version 3.4.1


Upgraded dependencies
~~~~~~~~~~~~~~~~~~~~~

The version requirements have changed for these dependencies:

* :mod:`django` must be any version from the *1.8* series.
* :mod:`djangorestframework` must be any version in either the *3.5* or *3.6* series.
* :mod:`django-filter` must be any version of the *1.0* series.
* :mod:`django-crispy-forms` must be any version of the *1.7* series.
* :mod:`crispy-forms-foundation` must be any version of the *0.6* series.
* :mod:`python-ldap` must be any version of the *3.0* series.
* :mod:`sphinx` must now be at least *1.8.0*.

Obsolete dependencies
~~~~~~~~~~~~~~~~~~~~~

* :mod:`django-hstore` is no longer needed, as HStore support is included in
  newer Django versions.

Build system rewrite and source code directory layout
-----------------------------------------------------

The entire build system has been rewritten, moving from GNU automake to regular
Python setuptools (since NAV has been mostly Python for years now). This also
means a lot of files in the source code tree have moved around to suit a more
Python-centric way of installing things - that is, many "data" files have been
moved into suitable Python packages:

`templates`
  The global :file:`templates` directory was moved to
  :file:`python/nav/web/templates`

`sql`
  All the SQL related scripts were moved to :file:`python/nav/models/sql`

`htdocs/sass`
  All SASS source files have moved to :file:`python/nav/web/sass`

`htdocs/static`
  All static web documents, including JavaScript sources, have
  been moved to :file:`python/nav/web/static`.

Instead of statically configuring filesystem paths and usernames into the NAV
code at build time, most of these variables are now configurable from config
files at runtime. Building and installing NAV now entails a sequence of::

  python ./setup.py build
  python ./setup.py install

See the updated installation guides for more detailed instructions.


Backwards incompatible changes
------------------------------

Changed command line options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some of the NAV programs have changed their command line interface:

* :program:`alertengine.py`: The nonworking ``--loglevel`` option was removed.
* :program:`pping.py`: The ``-n/--nofork`` option was renamed to ``-f/--foreground``.
* :program:`servicemon.py`: The ``-n/--nofork`` option was renamed to ``-f/--foreground``.
* :program:`smsd.py`: The ``-n/--nofork`` option was renamed to
  ``-f/--foreground``, while the ``-f/--factor`` option was renamed to
  ``-D/--delayfactor``.
* :program:`snmptrapd.py`: The ``-d/--daemon`` option was changed into a
  ``-f/--foreground``, while daemon mode was made the default.


Changed configuration files
~~~~~~~~~~~~~~~~~~~~~~~~~~~

These configuration files changed:

* :file:`nav.conf`: New options have been added. Some of these will be
  *required*, as the new build system will no longer build their values into
  the NAV binaries and libraries. All of them are present in the new example
  config file:

  ``NAV_USER``
    **REQUIRED**: Which user to run NAV processes as.
  ``PID_DIR``
    **REQUIRED**: Which directory to store process PID files in.
  ``LOG_DIR``
    **REQUIRED**: Which directory to store log files in.
  ``UPLOAD_DIR``
    Where to store images uploaded through the web interface. This option has a
    default value based on the system build parameters, but it is recommended to
    verify its value with your system.
* :file:`smsd.conf`: The ``loglevel`` option is no longer supported. Use
  :file:`logging.conf` to configure log levels.
* :file:`alertengine.conf`: The ``loglevel`` option is no longer supported. Use
  :file:`logging.conf` to configure log levels.

Changed daemon startup configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each of NAV's daemons had a corresponding shell script for controlling process
start/stop/reload in :file:`etc/init.d`, which were all invoked by the ``nav
start/stop`` set of commands. This has been *deprecated* in favor of a new YAML
configuration file, :file:`etc/daemons.yml`.

It was a common pattern for users to modify ipdevpoll's startup options inside
:file:`etc/init.d/ipdevpoll`, e.g. to enable :ref:`multiprocess mode
<ipdevpoll-multiprocess>`. If you previously did so, please migrate these start
options to the appropriate command section of :file:`daemons.yml`.



News
----

Interface browser
~~~~~~~~~~~~~~~~~

A new tool for browsing and searching interface information across all devices
in NAV has been added to the toolbox. Inspired by the new per-device interface
tab in IP Device Info, this more or less supplants the existing interface
reports in the report tool with a more dynamic tool based on NAV's already
existing REST API.

Interfaces can be filtered by device name, port type, port names and
descriptions, link status or VLAN. Thec olumns of the paged search results can
be customized, and can include sparklines of interface traffic counters.


Support for DNOS-SWITCHING MIB in PortAdmin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

With great support from Marcus Westin from the Linnaeus University who made
available equipment for testing, and Ludovic Vinsonnaud from Institut Optique
Graduate School who requested and supplied documentation from Dell, there is now
support for the DNOS-SWITCHING-MIB. This means that most Dell-devices now can be
configured using PortAdmin.

With Dell devices you can specify three modes for an interface - General, Access
and Trunk. NAV uses by default Q-BRIDGE-MIB to configure interfaces, but this
does not work for interfaces in Access mode - which is the default mode for the
interfaces. Thus to properly interact with Access mode support for Dells
DNOS-SWITCHING-MIB was implemented.

Partial support for IT WatchDogs / Geist V4 generation products
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The newest environment probes from IT WatchDogs / Geist have moved to new MIB
versions. The University of Tromsø has contributed partial support for
detecting sensors from these MIBs:

* ``IT-WATCHDOGS-V4-MIB``
* ``GEIST-V4-MIB``

"Partial" here means only internal sensors are supported - external sensors are
not, thus far.

Partial support for Powertek PDUs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The University of Tromsø has contributed partial support for collecting inlet
sensor data from Powertek PDUs. The implemented proprietary MIB is:

* ``PWTv1-MIB``

Support for HPE metered PDUs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Support for ``CPQPOWER-MIB`` has been implemented, so that all sensor readings
from HPE metered PDUs will be collected by NAV.

LDAP entitlement verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

NAV 4.9.6 adds entitlement verification as a possible filter step for
LDAP-based logins to the web interface. The new options are documented in
:doc:`the LDAP configuration docs </reference/ldap>`.


NAV 4.8
========

Dependency changes
------------------

The NAV team is currently working on removing some bundled libraries and
porting the NAV code to Python 3. Some previously bundled libraries have been
added to the dependency list, while others have had their required versions
changed.


New dependencies
~~~~~~~~~~~~~~~~

* :mod:`dnspython` == *1.15.0*
* :mod:`asciitree` == *0.3.3*
* :mod:`configparser` == *3.5.0*

Upgraded dependencies
~~~~~~~~~~~~~~~~~~~~~

The version requirements have changed for these dependencies:

* :mod:`IPy` == *0.83*
* Also, any version of :mod:`twisted` between *14.0.1* and *17.9.0* should work.
* :mod:`pynetsnmp` has been replaced with the :mod:`pynetsnmp-2` fork, which has better support for Python 3.

Removed dependencies
~~~~~~~~~~~~~~~~~~~~

* The support for the old **PySNMP v2** and **PySNMP-SE** libraries (and
  consequently, the pure-Python **TwistedSNMP** library) has been removed, since
  they are outdated and do not provide the full feature set used by NAV and
  provided by our preferred library: :mod:`pynetsnmp-2`.

* There is no longer a dependency to the Python module
  :mod:`django-oauth2-provider`, as NAV's usage of this non-maintained module
  was severely limited.

* :mod:`ipaddr` was removed. It was never a direct requirement of NAV. It only
  mentioned in the requirements list to satisfy a missing dependency of
  :mod:`pynetsnmp`, which has been rectified upstream, so it is still needed in
  a complete system.


Other changes
-------------

The :program:`navclean.py` program changed its name to simply
:program:`navclean`. If you were using it in any cron jobs or other scripts,
they will need to be updated.

News
----

Digital Optical Monitoring data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Retrieving data from optical transmit/receive sensors are now supported for
Cisco and Juniper devices. The values are graphed on the interface details
page for each applicable interface.

Power-over-Ethernet (PoE)
~~~~~~~~~~~~~~~~~~~~~~~~~

Power-over-Ethernet data is now collected and summarized for devices that
support the ``POWER-ETHERNET-MIB`` (:rfc:`3621`).

PoE information is found on a separate *PoE* tab on each device's IP Device
Info page, where an heuristic attempts to map PoE groups to modules within the
device.

There is still more work to be done on PoE-reporting, which will likely
require use of proprietary MIBs (which are also required for definitive
mapping between PoE groups and modules/interfaces, without using heuristics).

Topology improvements
~~~~~~~~~~~~~~~~~~~~~

The topology algorithm has been rewritten for improved processing of LLDP and
CDP topology information.

The topology detector now also supports detection of unrouted VLAN topologies.
One *caveat* of this, though, is that VLANs are now also discovered on
switches, using the VLAN names configured there. If your VLAN names aren't
consistent between your switches and routers, you may find multiple instances
of the same VLAN in your NAV (as the names are mapped to *netidents* in NAV,
where differing netidents imply separate broadcast domains).

New port listing in IP Device info
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The old "module-matrix" based port layout in IP Device Info has been replaced
with a more dynamic table listing of all interfaces. This table can be
searched, sorted and filtered dynamically on many interface parameters.

Users who prefer the old layout can choose switch back to it if they want, but
it will be removed in a later NAV version. Do not forget to give feedback to
you nearest friendly NAV developer :-)


Writable APIs
~~~~~~~~~~~~~

The API endpoints for netboxes and rooms have been write-enabled. When issuing
API tokens through the Useradmin panel, you can select the access level of any
token (all pre-existing tokens will be read-only until you say otherwise).

Check out the :doc:`REST API documentation </howto/using_the_api>` for more.

Mitigating slow IP Device deletion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It has been a known issue for years that a device that has been monitored by
NAV for a long time, will take an equally long time to delete from NAV. Old
devices have accrued lots and lots of related data in the PostgreSQL database,
and by not deleting old ARP and CAM logs, PostgreSQL essentially needs to
remove the IP device relation from all the old log entries, rather than delete
the log entries themselves. This gets slower the more data needs to be updated.

Deletion of IP Devices from SeedDB now runs as a background job (the
``navclean`` cron job, running by default every 5 minutes). SeedDB will only
mark a device as *"to be deleted"*, meaning it will still be visible in parts
of the interface until the PostgreSQL delete transaction has completed in the
background.

E-Mail reports
~~~~~~~~~~~~~~

The business reports tool now has the option to add e-mail subscriptions to
the available reports. Very good for people wearing neckties (or who need to
report to people wearing neckties on a regular basis).

Other improvements
~~~~~~~~~~~~~~~~~~

* Locations now have their own details page, with a image upload function,
  analogous to rooms.

* A new widget for showing active alerts grouped by location, analogous to the
  room alerts widgets, has been added.

* The source of any ARP record will now be reported in a separate column of
  Machine Tracker IP search results, if the *"source"* checkbox was checked.
  This can be helpful if you are experience "duplicate" entries, such as in
  HSRP/VRRP LANs.

* Removing a trunk from PortAdmin has been made into a much simpler,
  one-button operation.

* The HTTP and HTTPS service checkers will accept 401 responses as OK if no
  authentication credentials were given in the service checker's
  configuration.

* Neighboring nodes can now be filtered based on category from the Neighbors
  tab of IP Device Info.


NAV 4.7
========

Dependency changes
------------------

NAV 4.7 changes the minimum version requirement for three of its dependencies:

* PostgreSQL must now be at least version *9.4*.
* :mod:`psycopg2` must now be at least version *2.4.5*.
* :mod:`twisted` must now be at least version *14.0.1*.

Support for monitoring BGP sessions
-----------------------------------

BGP session monitoring has been added as part of :program:`ipdevpoll`'s
``statuscheck`` job. BGP4-MIB (:rfc:`4273` is supported), as well as the draft
versions of BGP4V2-MIB that Cisco and Juniper have implemented in their own
enterprise trees (which means IPv6 BGP sessions are supported on Cisco and
Juniper).

Please ensure your :file:`ipdevpoll.conf` is updated to take advantage of the
new functionality.

A ``[bgp]`` section has been added to :file:`ipdevpoll.conf`, where the
``alert_ibgp`` option can be used to toggle whether BGP events should be
generated for iBGP sessions. Its default value is `True`, but this may not be
desirable in a full mesh network.

The new ``bgpState`` event includes the ``bgpDown`` and ``bgpEstablished``
alert types, which can be subscribed to in your alert profile.

There is no bespoke UI for listing known BGP sessions in 4.7.0, but there is a
BGP session report in the report tool.


ipdevpoll multiprocess mode rewritten
-------------------------------------

When monitoring a large enough network, ipdevpoll may not be able to perform
all its work using a single process. To take advantage of modern
multi-processor and multi-core systems, using ipdevpoll's multiprocess mode
may be an advantage.

The multiprocess mode has been rewritten so that instead of starting a
dedicated process for each job type, an arbitratry number of generic worker
processes can be started, and jobs are assigned to these in a round-robin
fashion.

The multiprocess option ``-m`` can be added to the ``OPTIONS`` variable of the
ipdevpoll startup script (:file:`etc/init.d/ipdevpoll`).

Support for more infrastructure monitoring
------------------------------------------

NAV 4.7 adds support for collecting sensor readouts from various data loggers,
power distribution units, and cooling devices, used in the latest HPC
infrastructure being deployed in the Norwegian research network. Among these
are:

- `The Comet MS6D data logger`_
- `Eaton Williams Cooling Distribution Units (CDU)`_
- `Lenovo (IBM) power distribution units (PDU)`_
- `Raritan power distribution units (PDU)`_
- `Rittal power distribution units (PDU)`_
- `Rittal liquid cooling package (in-row liquid coolers)`_

.. note:: If adding Lenovo PDUs to NAV, please select *SNMP v1*, as their SNMP
          v2c GET-BULK implementation is either broken or not implemented.
          GET-BULK is NAV's default operation for mass retrieval operations
          under v2c.


.. _`The Comet MS6D data logger`: http://www.cometsystem.com/products/monitoring-systems/ms6d-data-logger/reg-MS6D
.. _`Eaton Williams Cooling Distribution Units (CDU)`: http://eaton-williams.com/servercool/products/servercool.php
.. _`Lenovo (IBM) power distribution units (PDU)`: http://shop.lenovo.com/us/en/systems/servers/options/systemx/rack-power-infrastructure/power/
.. _`Raritan power distribution units (PDU)`: http://www.raritan.com/products/power-distribution
.. _`Rittal power distribution units (PDU)`: https://www.rittal.com/com-en/product/list.action?categoryPath=/PG0001/PG0229STV1/PG7274STV1/PGR11260STV1
.. _`Rittal liquid cooling package (in-row liquid coolers)`: http://www.rittal.com/com-en/product/list.action?categoryPath=/PG0001/PG0168KLIMA1/PGR1951KLIMA1/PG1023KLIMA1

Improved user interfaces for sensor/environment monitoring
----------------------------------------------------------

Device "Sensors" tab
~~~~~~~~~~~~~~~~~~~~

The ipdevinfo tab previously known as "*Power and fans*" is now named
"*Sensors*". The tab now includes a comprehensive listing of all the sensors
NAV has discovered on a device, regardless of whether it is able to collect
any data from them. Charts and thresholds are available for each one.

Room "Sensors in Racks" tab
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The room view now includes the new tab "Sensors in Racks". In this tab, you
can create customized groupings of environment sensors present in a single
communications room.

At Uninett, this view is used to get an overview of the power load and cooling
water temperature on a per-rack basis in large HPC installations. PDU sensors
can nbe added to the left and right side of each "rack", and arbitrary sensors
from other types of devices can be added to the center column.


Avoiding redundant SNMP polling for virtual device contexts
-----------------------------------------------------------

A new feature enables you to use SeedDB to specify that an IP device is a
virtual instance of a physical "master" device. This can be useful if you use
Cisco VRF or VDC technologies extensively.

NAV will avoid polling interface counters, system and sensor data from the
virtual devices, but will instead duplicate the data collected from the master
device - thus avoiding overloading the physical device with redundant SNMP
requests.

This feature was sponsored by the University of Basel, Switzerland.


Changes to bulk import formats
------------------------------

The IP Device (Netbox) bulk import format has changed. Two new columns have
been added, so that the format is now specified as::

    roomid:ip:orgid:catid[:snmp_version:ro:rw:master:function:data:netboxgroup:...]

The new columns are:

snmp_version
  Selecting an explicit SNMP version was made compulsory in NAV 4.6, but the
  bulk import format was not updated in the same release, so any device added
  through the SeedDB bulk import function would default to SNMP v2c. Valid
  values here are 1 or 2.

master
  If this device is a virtual instance on another physical device, specify the
  sysname or IP address of the master in this column. You may have to bulk
  import multiple times if the master devices are part of the same bulk import
  file.

Support for dashboard export/import
-----------------------------------

Dashboard configurations can now be exported as JSON strings and shared with
other NAV users. Want to copy your colleagues fancy dashboard without putting
in all the work of setting it up manually? Now you can!

Audit logging
-------------

The beginnings of a full fledged audit logging system is included in NAV 4.7.
As of NAV 4.7.0, only changes made by users of PortAdmin will be audited.
Audit logging from more parts of NAV will follow.


NAV 4.6
========

Dependency changes
------------------

NAV now requires the :mod:`markdown` Python library, to ensure proper
rendering of documentation in the browseable API.

The :mod:`IPy` Python library is now required to be at least version *0.81*.


IPAM (IP Address Management)
----------------------------

This release introduces the IP Address Management tool, sponsored by the
Norwegian University of Science and Technology (NTNU).

Inspired by the already existing Subnet Matrix tool (reachable from NAV's
Report tool), IPAM was developed to assist in IP address management tasks,
using NAV's existing IP address prefix registry.

NTNU has, like many other higher education institutions in Norway have lately,
been merged with several other institutions, vastly increasing the number of
assigned IP address blocks to manage.

Whereas the Subnet Matrix can visualize a single network scope at a time, IPAM
was built to visualize multiple scopes interactively, and to allow for the
visualization of nested scopes. The tool includes search and filtering
capabilities, including functions to search for unallocated subnets of
specificed sizes and mark them as reserved (via SeedDB).


Static routes
-------------

Along with the IPAM tool, comes the new opt-in ipdevpoll plugin
`staticroutes`. This plugin re-implements the static routes plugin from
:program:`getDeviceData` (the pre NAV 3.6 collector), providing you with the
option of a more complete IP prefix registry.

If you wish to automatically collect statically configured routes from your
routers into NAV's prefix registry, you can add this plugin to you inventory
job - or, since your static route configuration isn't likely to change very
often, configure a separate ipdevpoll job with a much larger interval (e.g. 24
hours).

Collecting a router's entire routing table via SNMP can be taxing for some
routers, which is why this plugin is not enabled by default. The plugin can
also be configured to throttle the rate at which it sends SNMP requests to
routers.


Prefix information page and usage tags
--------------------------------------

A new per-prefix information page has been added, complementing the VLAN
information page.

As before, NAV will automatically collect the usage category of VLANs/subnets
based on the NTNU router port description convention, if this is employed.
Now, prefixes can be tagged with additional usage categories manually, through
the new prefix information page.

Valid usage categories are, as before, editable through SeedDB


Link aggregation support
------------------------

Information about any type of aggregated link discoverable through the
``IEEE8023-LAG-MIB`` (LACP) is collected and stored in NAV.

A new event type, ``aggregateLinkState``, with the accompanying
``linkDegraded`` and ``linkRestored`` alerts has been introduced. If link is
lost on an interface known to be part of such an aggregate it will cause NAV to
generate a ``linkDegraded`` alert for the aggregated interface.

Aggregation status of ports is also displayed in each port's details page.


Multi- and fullscreen dashboards
--------------------------------

Users can now have multiple named dashboards. A default dashboard can be
selected, which will be the first dashboard loaded when browsing the NAV front
page. Any "add graph to dashboard"-type button in NAV will add widgets to your
default dashboard, and widgets can easily be moved between dashboards.

A new "Compact dashboard" mode maximizes your screen real estate, by scaling
down the content and removing the spacing between widgets, while a new
fullscreen mode takes your dashboard and browser into full screen mode, using
the browser fullscreen API.

Each dashboard is individually configured using the dashboard menu to the
right. This enables you, for instance, to have a different number of columns
for each dashboard.


New dashboard widgets
---------------------

New dashboard widgets are introduced:

Alert
  This widget can monitor binary sensor values or arbitrary Graphite metrics
  of a an otherwise boolean nature, to be used as an alert indicator. Uninett's
  use-case for this is showing the status of the server room physical security
  system on the NOC screens.

PDU load
  A very specific plugin to display the power load status of APC power
  distribution units (these are the only PDU units currently known to be
  supported by NAV) on a room-by-room basis. Uninett's use-case for this is
  planning rack placements based on power consumption.

UPS status
  A graphical widget to display the inputs, outputs and status of any
  NAV-supported UPS.

Rooms with active alerts
  A version of the status widget that aggregates and summarizes alerts by
  room.


Hierarchical locations
----------------------

Hierarchies of locations can now be defined. SeedDB will now present locations
as a tree of entries, and parent locations can be selected from a dropdown
when adding a new location.

Selecting a location for a maintenance task, will implicitly include its full
sub-hierarchy of locations, as will filtering on locations in the status tool.

Location hierarchies are not yet respected by alert profiles and the Netmap.

Please note that the bulk import format for locations has changed to include the
parent location as the second field. Both the ``parent`` and the ``description``
fields are now optional. This makes it consistent with how organizations are
imported.

Business reports
----------------

A new "Business reports" tool was added. This tool is meant for more complex
reports than the pure SQL tabular reports NAV already sports. Each report must
be implemented as Python code.

Currently, two reports are implemented: A monthly device availability report
(with selectable months), and a monthly link availability report (with
selectable months). Both reports are based on NAV's alert history.


Juniper EX switch series workaround
-----------------------------------

If you have Juniper EX switches, you may be interested in the new
``juniperdot1q`` :program:`ipdevpoll` plugin, as a replacement for the regular
``dot1q`` plugin.

Juniper's implementation of ``Q-BRIDGE-MIB`` (the main MIB module used to
retrieve information about 802.1Q VLAN configuration) has multiple bugs,
several of which Juniper will not admit are bugs. The main issue for any NMS
using this MIB to get VLAN information is that parts of their implementation
uses opaque, internal VLAN IDs instead of public VLAN tags.

You may already have seen that the VLANs NAV has discovered on your EX
switches seem wrong. This is due to that implementation bug. The
``juniperdot1q`` plugin will use a Juniper proprietary MIB, if supported by
the device, to translate internal VLAN ids to public VLAN tags.

This functionality was implemented as a separate plugin, due to the pernicious
nature of the Juniper bugs. If you wish to test the plugin, simple replace the
reference to the ``dot1q`` plugin with ``juniperdot1q`` in the
:file:`ipdevpoll.conf` section ``[job_inventory]``.


navuser command line
--------------------

A new command line program, :program:`navuser`, has been introduced. This
program provides some simple means of manipulating NAV (web) accounts from the
command line, which can be useful from a configuration management perspective.



NAV 4.5
========

To see the overview of scheduled features and reported bugs on the 4.5 series
of NAV, please go to https://launchpad.net/nav/4.5 .

Dependency changes
------------------

There are none :-)

Cabling and patches
-------------------

The cabling and patch registry was introduced originally with NAV 3.0, but
never gained widespread usage, and had therefore fallen behind the rest of
NAV.

The University of Linköping has graciously sponsored a reworking of the SeedDB
cabling and patch forms, so that these are now actually usable in a NAV
installation with more than a handful of switches, cables and patches.
Information about patch points is now also displayed on each port's ipdevinfo
page.


navstats
--------

NAV 4.5 adds a simple program, `navstats`, that can be used to periodically
extract stats from the NAV database and store those stats as Graphite metrics.
To configure your own stats, however, you need to know your way around SQL and
the NAV DB schema.

For more information, see the `navstats` reference documentation.

API changes
-----------

API tokens can now be managed more flexibly via the User Admin tool. Multiple
tokens can be issued and revoked separately. Each token has its own expiry
time and list of authorized API endpoints.



NAV 4.4
=======

Dependency changes
------------------

- The Python library :mod:`django` must now be version *1.7*.
- The Python library :mod:`djangorestframework` must now be version *2.4*.
- The Python Imaging Library (PIL) seems dead and appears to no longer be
  available in the Python Package Index. We have replaced the dependency with
  :mod:`Pillow`, which is a fork of PIL. NAV should still work with the old
  library, though.

Interactive trend graphs
------------------------

Whereas NAV 4.3 and earlier would call on graphite-web to produce graphs as
static PNG images, NAV 4.4 uses the Rickshaw Javascript library to render
graphs from the same Graphite data.

These graphs allow for more user interaction, such as zooming and value
inspection. The are, however, not as readily re-usable by passing around URLs.


Slack dispatcher
----------------

NAV 4.4 adds a Slack dispatcher to the Alert Engine.

To dispatch messages to a Slack channel, you need to create a Slack channel and
add an Incoming Webhooks integration. More information about that can be found
at https://api.slack.com/incoming-webhooks . You will get an URL to use for
posting messages.

Then you need to add a Slack alert address to your alert profile and use this
address in an alert subscription. The address is the URL you got when setting up
the webhooks integration.

The username, emoji user-icon and channel for the messages are defined when
setting up the integration, but if you for some reason want to override this you
can do it in alertengine.conf.


Subnet matrix improvements
--------------------------

Various mysterious layout bugs in the subnet matrix have been fixed, by way of
a partial rewrite. Utilization data is now retrieve asynchronously, which
means that the matrix itself should load a lot faster. More details of each
subnet is now available in pop-up menus when clicking on them.


checkService.py has been renamed
--------------------------------

If you were using `checkService.py` to test your servicemon plugins, this
command has now been renamed to `navcheckservice`, and its command line
options have slightly changed. Run it with `--help` for more information.



NAV 4.3
=======

To see the overview of scheduled features and reported bugs on the 4.3 series
of NAV, please go to https://launchpad.net/nav/4.3 .

Dependency changes
------------------

There are none (unless you are a developer, then you should upgrade to the
latest version of pylint).

Data model changes (chassis, serial numbers, virtual devices, etc.)
-------------------------------------------------------------------

The 4.3 release changes NAV's data model in a fundamental way. Previously, NAV
would equate an IP device (a Netbox) with a piece of physical hardware, a
chassis, possibly with a retrievable serial number. This has become a rather
antiquated view in modern computer networking, where multiple virtual
components can be built from a single hardware unit, or a virtual device can
be built by stacking multiple hardware units.

The old data model would require each IP Device to have a unique serial
number, and also for any module in any IP Device to have a unique serial
number among all modules in all IP Devices.

NAV no longer has these restrictions. The hierarchy of physical entities
within an IP Device are collected from the ENTITY-MIB::entPhysicalTable, if
available, and all stored in the NAV database. NAV would previously only use
parts of this information.

A SNMP-less IP Device will no longer have a corresponding (physical) Device
entry, while a multi-chassis stack (like a Cisco VSS) will have all its
chassis registered in the database.

A set of Cisco VDCs defined within the same hardware unit will all present
themselves as physically identical to the hardware unit. Previously, this
would work poorly with NAV, because if its uniqueness requirement on serial
numbers.

Next, we aim to write support for collecting this type of hardware information
from Juniper devices, which, as of this writing, only support proprietary MIBs
to provide this information.

Bulk import format change
~~~~~~~~~~~~~~~~~~~~~~~~~

Because of the changed data model, the serial number column in the IP Device
(Netbox) bulk import/dump format has been removed. If you have old dump files
that you want to bulk import into NAV 4.3's SeedDB, you must remove the serial
number field from these files first.


The new chassisState family of alerts
-------------------------------------

NAV 4.3 introduces the ``chassisState`` event type, with ``chassisDown`` and
``chassisUp`` alerts. These can be subscribed to in Alert Profiles.

In a scenario where an IP Device is a stack of multiple physical chassis, NAV
will produce ``chassisState`` events if a previously known chassis disappears
or reappears in the stack. A chassis that is removed from a stack on purpose
must be manually deleted from NAV, just as purposefully removed modules have
always needed to be.

The eventengine will further suppress ``moduleDown`` alerts for modules that
reside within a chassis that has an active ``chassisDown`` alert. Previously,
a Cisco VSS that broke down would cause NAV to report a slew of ``moduleDown``
alerts, one for each of the modules in the lost chassis.


Deleting out of service modules and chassis
-------------------------------------------

When you physically remove a module to take it out of service, NAV will
produce a ``moduleDown`` alert. To remove the module from NAV's inventory, you
would previously need to go to the Device History tool and remove it from the
"Delete module" tab.

In NAV 4.3, deleting modules and (now) chassis, and their corresponding alerts
is directly available as one of the bulk actions on the status page.

Link, module and chassis status verification
--------------------------------------------

As part of the ipdevpoll ``inventory`` job, the ``modules`` and ``entity``
plugins (which both collect inventory and performs status check against known
inventory) only run every 6 hours. This is not often enough to provide a
continuous status verification (and updated alerts).

In response to this, the 5-minute interval ipdevpoll ``linkcheck`` job has
been renamed to the more generic ``statuscheck``, and the ``modules`` and
``entity`` plugins now additionally run as part of this job.


NAV 4.2
========

To see the overview of scheduled features and reported bugs on the 4.2 series
of NAV, please go to https://launchpad.net/nav/4.2 .

Dependency changes
------------------

There are none :-)

Rename some of your Whisper files to keep your statistics
---------------------------------------------------------

The 4.2.2 release adds commas to the list of characters escaped in Graphite
metric names; commas cause problems when constructing target names for
graphite-web, when rendering graphs and retrieving metrics. An out-of-place
comma will cause Graphite render requests to fail.

If your Graphite storage directory contains Whisper files with commas in
their filenames (under the `nav` hierarchy), and you want to keep your data
history, you will need to rename these files by replacing the commas with
underscores. Something like this should do the trick::

    cd /opt/graphite/storage/whisper/nav
    find -name '*,*' | xargs rename --verbose 's/,/_/g'


Multicast listener stats from IGMP snooping
-------------------------------------------

NAV 4.2 will use HP's STATISTICS-MIB to sum up the number of known multicast
group subscribers per HP switch (i.e. from each switch's IGMP snooping data).
Each multicast group address seen is logged to Graphite under the
`nav.multicast` hierarchy.

We wanted to support similar functionality for Cisco devices, but it seems
support for Cisco's own proprietary CISCO-IGMP-SNOOPING-MIB is very poor among
Cisco switches.


Graphite storage schema changes
-------------------------------

Be aware that the example Graphite storage schema
:file:`etc/nav/graphite/storage-schema.conf` has added a section for multicast
statistics. Be sure to update your running Carbon configuration.

Rewritten Status tool
---------------------

The Status tool has been rewritten from scratch.

The old Status tool hardcoded table listings for specific alert types, and not
all alert types were supported - meaning some alerts were never actually
displayed in the Status tool. This also made it very difficult to dynamically
add new alert types from plugins or third party software, without modifying
the Status tool code.

The new tool offers an in-page status filtering form, which can also be saved
as your personal status page filter preference.

Any filter configuration can also be saved as a new front-page status filter,
meaning you can have multiple status widgets, each with a different
configuration. When modifying the default/anonymous user's front page widgets,
this means you can also decide which types of alerts, if any, will be
displayed to unauthenticated users.

Alert acknowledgement
~~~~~~~~~~~~~~~~~~~~~

With the new Status tool comes the ability to acknowledge open alerts, with
comments. An acknowledged alert is not displayed under the default Status tool
filter configuration (but can be added by checking the "Acknowledged"
checkbox).

Stateless alerts
~~~~~~~~~~~~~~~~

The Status tool normally displays stateful alerts, i.e. states that have a
starting time and, eventually, an ending time. The can be actual problems, or
more information states, such as a device being on scheduled maintenance.

However, NAV will at times also issue stateless alerts (warnings). Before,
these were normally only accessible in the Device History tool, and through
alert subscriptions in Alert Profiles.

The Status page tool can now be configured to include recent stateless alerts,
within a set threshold (the default is 24 hours). The default is still to
leave them out.

New status widget
~~~~~~~~~~~~~~~~~

A widget version of the new Status tool is also introduced. Users who have the
old Status widget on their NAV front pages will see their widgets replaced
with a Status tool widget filtering for *boxState* events.

By default, NAV places a status widget on the front page of anonymous users.
With the new widget, you can also control what kind of alerts anonymous users
can see on the front page.

.. TIP:: To configure, remove or add more Status widgets to the front page of
         anonymous users, go to the User Admininstration tool, select the
         *default* user and click the button :guilabel:`Operate as this user`.

         While operating as the *default* user, configure the widgets on the
         front page to your liking. Click :guilabel:`Log back in as ...` to
         return to normal operation.


Netmap redesign
---------------

There was never time to clean up the Netmap tool's complicated user interface
during the design changes released in NAV 4.0. This has now been rectified.

The map portion of the page has been given more space, and the view options
are now contained in a hideable panel above the map. Your saved views should
still work.


SeedDB IP device form redesign
------------------------------

The form for adding and editing an IP device has been redesigned. It no longer
requires connectivity to add or edit an IP device, but you have the option to
verify the connectivity if you want. As a result of this, only one step is
required to complete the form. Should you go ahead and save a router with the
wrong SNMP community, NAV will shortly raise an *snmpAgentAlert* for this
device.

In addition to this, IP address verification has been added to the form. When
adding an IP device by its hostname in NAV versions prior to 4.2, if this
hostname resolved to multiple IP addresses, NAV would select an arbitrary IP
address from these as its management address for the device. The new form will
ask the user to choose one of the resolved IP addresses from a list.


Custom attributes on IP devices and locations
---------------------------------------------

You now have to option to add custom attributes to your IP devices and
locations. In NAV 4.1 this was only available for rooms and organizations. The
custom attributes are added in the respective SeedDB forms.

The attributes added for IP devices are displayed on the IP Device Info page.
The attributes for locations are currently not visible outside of SeedDB, as
there are no canonical Location-pages in NAV (yet). The *location* report can
be amended locally to include those attributes you want displayed, in the same
way as commented on the *organization* and *room* reports.


New command line utilities
--------------------------

NAV 4.2 introduces three new command line utilities for advanced users:

navdf
~~~~~
::

    Usage: navdf [filter]

    Lists and filters IP devices monitored by NAV

    Options:
      -h, --help  show this help message and exit

    The filter expression must be a method call applicable to the Django-based
    Netbox model's manager class. Example: "filter(category__id='GSW')"


navoidverify
~~~~~~~~~~~~
::

    usage: navoidverify baseoid < sysnames.txt

    Verifies SNMP sub-tree support on a set of NAV-monitored devices

    positional arguments:
      baseoid     The base OID for which a GETNEXT operation will be performed

    optional arguments:
      -h, --help  show this help message and exit

    Given the root of an SNMP MIB module, a bunch of devices can be queried in
    parallel whether they have any objects below the given BASEOID - effectively
    verifying MIB support in these devices.


naventity
~~~~~~~~~
::

    usage: naventity device

    Outputs entity hierarchy graph from a device's ENTITY-MIB::entPhysicalTable
    response

    positional arguments:
      device      The NAV-monitored IP device to query. Must be either a sysname
		  prefix or an IP address.

    optional arguments:
      -h, --help  show this help message and exit


Files to remove
---------------

Many files have been removed or moved around since NAV 4.0 and 4.1. Unless you
upgraded NAV using a package manager (such as APT), you may need/want to
remove some obsolete files and directories (here prefixed by /usr/local/nav)::

    /usr/local/nav/doc/hacking/netmap.rst
    /usr/local/nav/doc/hacking/using-vagrant.rst
    /usr/local/nav/doc/hacking/vagrant.rst
    /usr/local/nav/doc/html/hacking/netmap.html
    /usr/local/nav/doc/html/hacking/using-vagrant.html
    /usr/local/nav/doc/html/hacking/vagrant.html
    /usr/local/nav/doc/html/_sources/hacking/netmap.txt
    /usr/local/nav/doc/html/_sources/hacking/using-vagrant.txt
    /usr/local/nav/doc/html/_sources/hacking/vagrant.txt
    /usr/local/nav/lib/python/nav/web/api/auth.py
    /usr/local/nav/lib/python/nav/web/api/helpers/
    /usr/local/nav/lib/python/nav/web/api/serializers.py
    /usr/local/nav/lib/python/nav/web/api/views.py
    /usr/local/nav/lib/python/nav/web/netmap/forms.py
    /usr/local/nav/share/htdocs/static/js/src/netmap/app.js
    /usr/local/nav/share/htdocs/static/js/src/netmap/collections/
    /usr/local/nav/share/htdocs/static/js/src/netmap/main.js
    /usr/local/nav/share/htdocs/static/js/src/netmap/models/
    /usr/local/nav/share/htdocs/static/js/src/netmap/order.js
    /usr/local/nav/share/htdocs/static/js/src/netmap/resource.js
    /usr/local/nav/share/htdocs/static/js/src/netmap/router.js
    /usr/local/nav/share/htdocs/static/js/src/netmap/templates/
    /usr/local/nav/share/htdocs/static/js/src/netmap/views/
    /usr/local/nav/share/templates/netmap/admin_list_mapviews.html
    /usr/local/nav/share/templates/netmap/backbone.html
    /usr/local/nav/share/templates/netmap/graphml.html


NAV 4.1
========

To see the overview of scheduled features and reported bugs on the 4.1 series
of NAV, please go to https://launchpad.net/nav/4.1 .

Dependency changes
------------------

New dependencies:

- The Python module :mod:`django-filter` >= 0.5.3
- The Python module :mod:`django-hstore` >= 0.2.4
- The PostgreSQL extension ``hstore`` - may or may not be part of your default
  PostgreSQL server installation.


Schema changes and hstore
-------------------------

PostgreSQL's hstore extension has been utilized to implement the new
flexible attribute feature for organization and room records.

The hstore extension has been distributed with PostgreSQL since version 9, but
will on some Linux distros be shipped in a separate package from the
PostgreSQL server package. In Debian, for example, the ``postgresql-contrib``
package must be installed to enable the extension.

The :command:`navsyncdb` command will automatically install the hstore
extension into the NAV database if missing, but the installation requires
superuser access to the database. Normally, this is only required when
initializing the database from scratch, using the ``-c`` option.
Typically, if NAV and PostgreSQL are on the same server, :command:`navsyncdb`
is invoked as the ``postgres`` user to achieve this (otherwise, use the
:envvar:`PGHOST`, :envvar:`PGUSER`, :envvar:`PGPASSWORD` environment variables
to connect remotely as the ``postgres`` user)::

  sudo -u postgres navsyncdb

Watchdog
--------

NAV 4.1 implements the first version of the Watchdog system, which is
responsible for monitoring NAV's internal affairs. This new tool can be used
to detect problems with NAV's data collection, among other things. Its primary
status matrix is also available as a widget that can be added to your front
page.

A future planned feature is generating NAV alerts based on problems detected
by the watchdog system.


New REST API
------------

NAV 4.0 shipped with some experimental, undocumented API calls. These have
been deprecated, and new API endpoints have been written for NAV 4.1.

Although the API is still in flux, it can be used to retrieve various data
from a NAV installation. See further documentation at
https://nav.readthedocs.io/en/latest/howto/using_the_api.html . We know a lot of
people are eager to integrate with NAV to utilize its data in their own
solutions, so any feedback you may have regarding the API is much appreciated
by the developers.


NAV 4.0
========

To see the overview of scheduled features and reported bugs on the 4.0 series
of NAV, please go to https://launchpad.net/nav/4.0 .

Dependency changes
------------------

New dependencies:

- Graphite_
- Sass_ >= 3.2.12 (only required at build time)
- The Python module :mod:`django-crispy-forms` == 1.3.2
- The Python module :mod:`crispy-forms-foundation` == 0.2.3
- The Python module :mod:`feedparser` >=5.1.2,<5.2

Changed version requirements:

- `Python` >= 2.7.0

Removed dependencies:

- Cricket
- rrdtool

.. _Graphite: http://graphiteapp.org/
.. _Sass: http://sass-lang.com/

Major changes to statistics collection
--------------------------------------

NAV 4.0 ditches Cricket for collection and presentation of time-series data.
Cricket is great for manually maintaining large configurations, but becomes
quite inflexible when integrating with a tool like NAV. Also, Cricket has not
been actively developed since 2004.

Collection of time-series data via SNMP has become the responsibility of NAV's
existing SNMP collector engine, `ipdevpoll`, implemented as new plugins and
job configurations.

RRDtool has also been ditched in favor of Graphite_, a more flexible and
scalable system for storage of time-series data. Graphite provides a networked
service for receiving *"metrics"*, meaning it can be installed on a separate
server, if desirable. It will even scale horizontally, if needed.

The parts of NAV that collect or otherwise produce time-series data, such as
values collected via SNMP, ping roundtrip times or ipdevpoll job performance
metrics, will now send these to a configured Carbon backend (Graphite's
metric-receiving daemon).

Due to this extensive change, the threshold manager interface and the threshold
monitor have been rewritten from scratch. The new threshold monitoring system
uses *"threshold rules"*, which leverage functionality built-in to Graphite.
It is also essentially independent of NAV, which means it can also monitor
thresholds for data that was put into Graphite by 3rd party software.

Migrating existing data
-----------------------

Existing threshold values for RRD-based data sources cannot be consistently
migrated to the new threshold rule system, so you will need to configure your
threshold rules from scratch.

We do provide a program for migrating time-series data stored in RRD files
into Graphite, which will enable you to keep old data when upgrading from an
older NAV version. Usage and limitations of this program is documented in a
separate howto guide: :doc:`/howto/migrate-rrd-to-graphite`.

.. note:: If you wish to migrate time-series data, please read :doc:`the guide
          </howto/migrate-rrd-to-graphite>` **before** starting NAV 4.


Files to remove
---------------

Many files have been removed or moved around since NAV 3.15. Unless you
upgraded NAV using a package manager (such as APT), you may need/want to
remove some obsolete files and directories (here prefixed by /usr/local/nav)::

  /usr/local/nav/bin/cleanrrds.py
  /usr/local/nav/bin/extract_cricket_oids.py
  /usr/local/nav/bin/fillthresholds.py
  /usr/local/nav/bin/getBoksMacs.sh
  /usr/local/nav/bin/mcc.py
  /usr/local/nav/bin/migrate_cricket.py
  /usr/local/nav/bin/networkDiscovery.sh
  /usr/local/nav/bin/ping.py
  /usr/local/nav/bin/thresholdMon.py
  /usr/local/nav/etc/cricket-config/
  /usr/local/nav/etc/cricket-views.conf
  /usr/local/nav/etc/cron.d/cricket
  /usr/local/nav/etc/cron.d/thresholdMon
  /usr/local/nav/etc/mcc.conf
  /usr/local/nav/etc/subtree-sets
  /usr/local/nav/lib/python/nav/activeipcollector/rrdcontroller.py
  /usr/local/nav/lib/python/nav/ipdevpoll/plugins/oidprofiler.py
  /usr/local/nav/lib/python/nav/mcc/
  /usr/local/nav/lib/python/nav/netmap/rrd.py
  /usr/local/nav/lib/python/nav/statemon/rrd.py
  /usr/local/nav/lib/python/nav/web/cricket.py
  /usr/local/nav/lib/python/nav/web/rrdviewer/
  /usr/local/nav/share/htdocs/cricket/
  /usr/local/nav/share/htdocs/images/
  /usr/local/nav/share/htdocs/js/
  /usr/local/nav/share/htdocs/style/
  /usr/local/nav/share/templates/alertprofiles/address_tab.html
  /usr/local/nav/share/templates/alertprofiles/filter_group_tab.html
  /usr/local/nav/share/templates/alertprofiles/filter_tab.html
  /usr/local/nav/share/templates/alertprofiles/matchfield_tab.html
  /usr/local/nav/share/templates/alertprofiles/profile_tab.html
  /usr/local/nav/share/templates/devicehistory/history_view_filter.html
  /usr/local/nav/share/templates/devicehistory/paginator.html
  /usr/local/nav/share/templates/ipdevinfo/frag-datasources.html
  /usr/local/nav/share/templates/seeddb/tabs_cabling.html
  /usr/local/nav/share/templates/seeddb/tabs_location.html
  /usr/local/nav/share/templates/seeddb/tabs_netboxgroup.html
  /usr/local/nav/share/templates/seeddb/tabs_netbox.html
  /usr/local/nav/share/templates/seeddb/tabs_organization.html
  /usr/local/nav/share/templates/seeddb/tabs_patch.html
  /usr/local/nav/share/templates/seeddb/tabs_prefix.html
  /usr/local/nav/share/templates/seeddb/tabs_room.html
  /usr/local/nav/share/templates/seeddb/tabs_service.html
  /usr/local/nav/share/templates/seeddb/tabs_type.html
  /usr/local/nav/share/templates/seeddb/tabs_usage.html
  /usr/local/nav/share/templates/seeddb/tabs_vendor.html
  /usr/local/nav/share/templates/threshold/bulkset.html
  /usr/local/nav/share/templates/threshold/delete.html
  /usr/local/nav/share/templates/threshold/edit.html
  /usr/local/nav/share/templates/threshold/listall.html
  /usr/local/nav/share/templates/threshold/manageinterface.html
  /usr/local/nav/share/templates/threshold/managenetbox.html
  /usr/local/nav/share/templates/threshold/not-logged-in.html
  /usr/local/nav/share/templates/threshold/select.html
  /usr/local/nav/share/templates/threshold/start.html
  /usr/local/nav/share/templates/webfront/preferences_navigation.html
  /usr/local/nav/share/templates/webfront/toolbox_big_frag.html
  /usr/local/nav/share/templates/webfront/toolbox_small_frag.html
  /usr/local/nav/var/cricket-data/
  /usr/local/nav/var/log/cricket/


NAV 3.15
========

To see the overview of scheduled features and reported bugs on the 3.15 series
of NAV, please go to https://launchpad.net/nav/3.15 .

Dependency changes
------------------

New dependencies:

- `mod_wsgi`
- The following Python modules:
    - The Python Imaging Library (`PIL`, aka. `python-imaging` on Debian).
    - `django-oauth2-provider` >= 0.2.6
    - `djangorestframework` >= 2.3.7
    - `iso8601`

Changed version requirements:

- `Django` >= 1.4
- `PostgreSQL` >= 9.1

Removed dependencies:

- `mod_python`
- Cheetah Templates


Database schema changes
-----------------------

The database schema files have been moved to a new location, and so has the
command to synchronize your running PostgreSQL database with changes. The
syncing command previously known as :file:`syncdb.py` is now the
:program:`navsyncdb` program, installed alongside NAV's other binaries.


Configuration changes
---------------------

The configuration file :file:`nav.conf` has gained a new option called
`SECRET_KEY`. NAV's web interface will not work unless you add this option to
:file:`nav.conf`.

Set it to a string of random characters that should be unique for your NAV
installation. This is used by the Django framework for cryptographic signing
in various situations. Here are three suggestions for generating a suitable
string of random characters, depending on what tools you have available:

    1. :code:`gpg -a --gen-random 1 51`
    2. :code:`makepasswd --chars 51`
    3. :code:`pwgen -s 51 1`

Please see
https://docs.djangoproject.com/en/1.4/ref/settings/#std:setting-SECRET_KEY if
you want to know more about this.


mod_python vs. mod_wsgi
-----------------------

NAV no longer depends on `mod_python`, but instead leverages Django's ability
to serve a NAV web site using its various supported methods (such as `WSGI`,
`flup` or `FastCGI`).

This strictly means that NAV no longer is dependent on `Apache`; you should be
able to serve it using *any web server* that supports any of Django's methods.
However, we still ship with a reasonable Apache configuration file, which now
now uses `mod_wsgi` as a replacement for `mod_python`.

.. WARNING:: If you have taken advantage of NAV's authentication and
             authorization system to protect arbitrary Apache resources, such
             as static documents, CGI scripts or PHP applications, you **will
             still need mod_python**. This ability was only there as an upshot
             of `mod_python` being Apache specific, whereas `WSGI` is a
             portable interface to web applications.

NAV 3.15 still provides a `mod_python`-compatible module to authenticate and
authorize requests for arbitrary Apache resources. To protect any resource,
make sure `mod_python` is still enabled in your Apache and add something like
this to your Apache config:

.. code-block:: apacheconf

  <Location /uri/to/protected-resource>
      PythonHeaderParserHandler nav.web.modpython
  </Location>

Access to this resource can now be controlled through the regular
authorization configuration of NAV's Useradmin panel.


REST API
--------

NAV 3.15 also includes the beginnings of a read-only RESTful API. The API is
not yet documented, and must be considered an unstable experiment at the
moment. API access tokens can only be issued by a NAV administrator.


Write privileges for room image uploads
---------------------------------------

Uploaded images for rooms are stored in
:file:`${prefix}/var/uploads/images/rooms/`. This directory needs to be
writable for navcron, assuming you are using the default wsgi setup.


Files to remove
---------------

Some files have been moved around. The SQL schema files are no longer
installed as part of the documentation, but as data files into a subdirectory
of whichever directory is configured as the datadir (the default is
:file:`${prefix}/share`). The Django HTML templates have also moved into a
subdirectory of datadir. Also, almost all the documentation source files have
changed their file name extension from .txt to .rst to properly indicate that
they employ reStructuredText markup.

If any of the following files and directories are still in your installation
after upgrading to NAV 3.15, they should be safe to remove (installation
prefix has been stripped from these file names). If you installed and upgraded
NAV using a packaging system, you should be able to safely ignore this
section::

  bin/navTemplate.py

  doc/*.txt
  doc/faq/*.txt
  doc/intro/*.txt
  doc/reference/*.txt

  doc/cricket/
  doc/mailin/
  doc/sql/

  etc/cricket-config/router-interfaces/
  etc/cricket-config/switch-ports/

  lib/python/nav/django/shortcuts.py
  lib/python/nav/django/urls/*
  lib/python/nav/getstatus.py
  lib/python/nav/messages.py
  lib/python/nav/report/utils.py
  lib/python/nav/statemon/core.py
  lib/python/nav/statemon/execute.py
  lib/python/nav/statemon/icmp.py
  lib/python/nav/statemon/ip.py
  lib/python/nav/statemon/mailAlert.py
  lib/python/nav/statemon/Socket.py
  lib/python/nav/statemon/timeoutsocket.py
  lib/python/nav/topology/d3_js
  lib/python/nav/topology/d3_js/d3_js.py
  lib/python/nav/topology/d3_js/__init__.py
  lib/python/nav/web/encoding.py
  lib/python/nav/web/noauth.py
  lib/python/nav/web/seeddb/page/subcategory.py
  lib/python/nav/web/state.py
  lib/python/nav/web/templates/__init__.py
  lib/python/nav/web/webfront/compability.py

  lib/python/nav/web/templates/
  lib/templates/

  share/htdocs/js/arnold.js
  share/htdocs/js/d3.v2.js
  share/htdocs/js/default.js
  share/htdocs/js/report.js
  share/htdocs/js/require_config.test.js
  share/htdocs/js/src/netmap/templates/algorithm_toggler.html
  share/htdocs/js/src/netmap/templates/link_info.html
  share/htdocs/js/src/netmap/templates/list_maps.html
  share/htdocs/js/src/netmap/templates/map_info.html
  share/htdocs/js/src/netmap/templates/netbox_info.html
  share/htdocs/js/src/netmap/templates/searchbox.html
  share/htdocs/js/src/netmap/views/algorithm_toggler.js
  share/htdocs/js/src/netmap/views/link_info.js
  share/htdocs/js/src/netmap/views/list_maps.js
  share/htdocs/js/src/netmap/views/map_info.js
  share/htdocs/js/src/netmap/views/netbox_info.js
  share/htdocs/js/src/netmap/views/searchbox.js
  share/htdocs/js/threshold.js
  share/htdocs/style/MatrixScopesTemplate.css
  share/htdocs/style/MatrixTemplate.css


NAV 3.14
========

To see the overview of scheduled features and reported bugs on the 3.14 series
of NAV, please go to https://launchpad.net/nav/3.14 .

Dependency changes
------------------

- The `pynetsnmp` library is still optional (for the time being) and
  recommended, but is **required** if IPv6 SNMP support is needed.

Manual upgrade steps required
-----------------------------

In NAV 3.14.1592, the Cricket trees `switch-ports` and `router-interfaces`
have been consolidated into a single `ports` tree, where all physical ports'
traffic stats now also are collected. After running the usual `syncdb.py`
command, you should run `mcc.py` once manually (as the navcron) user to ensure
the Cricket config tree is updated.

When everything is up and running again, you can optionally delete the
`switch-ports` and `router-interfaces` directories from your `cricket-config`
directory, as they are no longer used by NAV.

NAV now supplies its own `subtree-sets` configuration to Cricket. If you have
made manual changes to your Cricket collection setup and/or this file, you may
need to update your setup accordingly.


IPv6
----

NAV 3.14 supports SNMP over IPv6, and most of the service monitors can now
also support IP devices with an IPv6 address in NAV. When adding a service
monitor in SeedDB, any monitor that doesn't support IPv6 will be marked as
such.

NAV will also properly configure Cricket with IPv6 addresses, but Cricket's
underlying SNMP library *needs two optional Perl modules* to be installed to
enable IPv6. These modules are:

* `Socket6`
* `IO::Socket::INET6`

On Debian/Ubuntu these two are already in the Recommends list of the
`libsnmp-session-perl` package (Cricket's underlying SNMP library); depending
on your Apt configuration, they may or may not have been installed
automatically when the `cricket` package was installed.


Files to remove
---------------

If any of the following files and directories are still in your installation
after upgrading to NAV 3.14, they should be removed (installation prefix has
been stripped from these file names).  If you installed and upgraded NAV using
a packaging system, you should be able to safely ignore this section::

  etc/rrdviewer/
  lib/python/nav/statemon/checker/*.descr
  share/htdocs/js/portadmin.js


NAV 3.13
========

To see the overview of scheduled features and reported bugs on the 3.13 series
of NAV, please go to https://launchpad.net/nav/3.13 .

Dependency changes
------------------

- NAV no longer requires Java. Consequently, the PostgreSQL JDBC driver is no
  longer needed either.
- To use the new `netbiostracker` system, the program ``nbtscan`` must be
  installed.

New eventengine
---------------

The `eventengine` was rewritten in Python. The beta version does not yet
support a config file, but this will come.

There is now a single log file for the `eventengine`, the lower-cased
``eventengine.log``. The ``eventEngine.log`` log file and the ``eventEngine``
log directory can safely be removed.

New alert message template system
---------------------------------

As a consequence of the `eventEngine` rewrite, alert message templates are no
longer stored in the ``alertmsg.conf`` file. Instead, `Django templates`_ are
used as the basis of alert message templates, and each template is stored in
an event/alert hierarchy below the ``alertmsg/`` directory.

Also, NAV 3.13 no longer provides Norwegian translations of these templates.

The hierarchy/naming conventions in the ``alertmsg/`` directory are as follows::

  <event type>/<alert type>-<medium>.[<language>.]txt

The `<event type>` is one of the available event types in NAV, whereas `<alert
type>` is one of the alert types associated with the event type. `<medium>` is
one of the supported alert mediums, such as `email`, `sms` or `jabber`. A two
letter language code is optional; if omitted, English will be assumed.

To make a Norwegian translation of the ``boxState/boxDown-email.txt``
template, copy the file to ``boxState/boxDown-email.no.txt`` and translate the
text inside the copied file.

Variables available in the template context include:

* `source`
* `device`
* `netbox`
* `subid`
* `time`
* `event_type`
* `alert_type`
* `state`
* `value`
* `severity`

Some of these, such as the `netbox` variable, are Django models, and will
enable access to query related information in the NAV database. Various
attributes accessible through the `netbox` variable include:

* `netbox.sysname`
* `netbox.room`
* `netbox.room.location`
* `netbox.category`
* `netbox.organization`

Also, since `Django templates`_ are used, you have the full power of its
template tag library to control and customize the appearance of an alert
message based on the available variables.

.. _`Django templates`: https://docs.djangoproject.com/en/1.4/ref/templates/

VLANs
-----

It is now possible to search for VLANs in the navbar search. The search triggers
on VLAN numbers and netidents.

The VLAN page contains details about the VLAN and its related router ports and
prefixes. The information is linked to the more extensive reports for each
port and prefix.

The page also contains graphs of the number of hosts on the VLAN over time
(both IPv4 and IPv6 hosts, as well as number of unique MAC addresses seen).
Historic information is easily accessible by utilizing the buttons next to the
graphs.

Bootstrapping host count graphs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Collection of the number of active hosts on each VLAN starts as you upgrade to
NAV 3.13. The graphs will therefore have no information prior to this point.

The source information comes from NAV's logs of ARP and ND caches from your
routers. If you upgraded to 3.13 from a previous version, you can bootstrap
your graphs with historical information from NAV's database.

To do this, use the ``collect_active_ip.py`` program provided with NAV 3.13::

  Usage: collect_active_ip.py [options]

  Options:
    -h, --help            show this help message and exit
    -d DAYS, --days=DAYS  Days back in time to start collecting from
    -r, --reset           Delete existing rrd-files. Use it with --days to
                          refill

To bootstrap your graphs with data from the last year (this may take a while),
run::

  sudo -u navcron collect_active_ip.py -d 365 -r

.. NOTE:: NAV does not have historical information about prefixes. If your
          subnet allocations have changed considerably recently, you shouldn't
          bootstrap your graphs further back than this if you want your graphs
          to be as close to the truth as possible.


Arnold
------

Arnold was rewritten to not use ``mod_python`` and to use Django's ORM for
database access. The rewrite has tried to be as transparent as possible and at
the same time fix any open bugs reports.

Some changes are introduced:

- The shell script for interacting directly with Arnold is gone. If there is an
  outcry for it, it will be reintroduced. The other scripts for automatic
  detentions and pursuit are a part of the core functionality and are of course
  still present.

- The workflow when manually detaining has been slightly improved.

- The reasons used for automatic detentions are no longer available when
  manually detaining. This is done to be able to differ between manual and
  automatic detentions. If you detain for the same reason both manually and
  automatically, just create two similar reasons.

- Log levels are no longer set in ``arnold.conf``. Use ``logging.conf`` to
  alter loglevels for the scripts and web.

- Some unreported bugs are fixed.

- The “Open on move”-option in a predefined detention was never used. This is
  fixed.

- Pursuing was not done in some cases.

- Reported bugs that were fixed:
  - LP#341703 Manual detention does not pursue client
  - LP#361530 Predefined detention does not exponentially increase detentions
  - LP#744932 Arnold should give warning if snmp write is not configured

Files to remove
---------------

If any of the following files and directories are still in your installation
after upgrading to NAV 3.13, they should be removed (installation prefix has
been stripped from these file names).  If you installed and upgraded NAV using
a packaging system, you should be able to safely ignore this section::

  bin/arnold.py
  bin/eventEngine.sh
  etc/alertmsg.conf
  etc/eventEngine.conf (new config format in lowercase eventengine.conf)
  lib/java/
  lib/python/nav/web/arnoldhandler.py
  lib/python/nav/web/loggerhandler.py
  lib/python/nav/web/radius/radius.py
  lib/python/nav/web/report/handler.py
  var/log/eventEngine/


NAV 3.12
========

To see the overview of scheduled features and reported bugs on the 3.12 series
of NAV, please go to https://launchpad.net/nav/3.12 .

Dependency changes
------------------

- Python >= 2.6 is now required. NAV will not work under Python 3.
- Django >= 1.2 is now required. NAV will likely not work under Django 1.4.


Cricket configuration
---------------------

Your subtree-sets configuration for Cricket must be updated. This file is most
likely placed in /etc/cricket/. Compare manually with or copy from
`doc/cricket/cricket/subtree-sets`.

Take note of `$(NAV)/etc/mcc.conf`. Module `interfaces` should be there instead
of `routerinterfaces` and `switchports`.

IPv6 statistics for router interfaces will now be collected. For this to work
you need to copy some configuration templates to your `cricket-config`
directory.  NB: Make sure the `dataDir` is the same as the original after
copying the `Defaults` file. If your NAV is installed in `/usr/local/nav`, run
these commands::

  sudo cp doc/cricket/cricket-config/Defaults \
             /usr/local/nav/etc/cricket-config/

  sudo cp -r doc/cricket/cricket-config/ipv6-interfaces \
             /usr/local/nav/etc/cricket-config/

Room map
--------

If you have registered coordinates (latitude, longitude) on your rooms you may
include a geographical map of the rooms on the front page by editing
`etc/webfront/welcome-registered.txt` and/or `welcome-anonymous.txt` and
adding the following HTML::

  <div id="mapwrapper">
      <div id="room_map" class="smallmap"></div>
  </div>

If you feel like having a bigger map, replace `smallmap` with `bigmap`. The
markers are clickable and will take you to the new "Room view" for the clicked
room.

Toolbar search
--------------

The toolbar search now searches for more than IP devices. Try it!

Files to remove
---------------

If any of the following files and directories are still in your installation
after upgrading to NAV 3.12, they should be removed (installation prefix has
been stripped from these file names).  If you installed and upgraded NAV using
a packaging system, you should be able to safely ignore this section::

  doc/getting-started.txt
  doc/mailin/README
  doc/radius/
  etc/apache/subsystems/maintenance.conf
  etc/apache/subsystems/messages.conf
  etc/apache/subsystems/netmap.conf
  lib/python/nav/ipdevpoll/plugins/lastupdated.py
  lib/python/nav/web/maintenance/handler.py
  lib/python/nav/web/messages/handler.py
  lib/python/nav/web/netmap/datacollector.py
  share/htdocs/js/DeviceBrowserTemplate.js
  share/htdocs/js/devicehistory.js
  share/htdocs/js/EditTemplate.js
  share/htdocs/js/ipdevinfo.js
  share/htdocs/js/jquery-1.4.4.min.js
  share/htdocs/js/jquery-json-2.2.min.js
  share/htdocs/js/quickselect.js
  share/htdocs/js/seeddb.js
  share/htdocs/js/seeddbTemplate.js
  share/htdocs/netmap/


NAV 3.11
========

To see the overview of scheduled features and reported bugs on the 3.11 series
of NAV, please go to https://launchpad.net/nav/3.11 .

Dependency changes
------------------

- `JavaSNMP` is no longer a dependency and can be removed. There is also
  therefore no longer any need to export a `CLASS_PATH` variable before
  building NAV from source.

Topology source data
--------------------

The getBoksMacs Java program has been replaced by a set of ipdevpoll plugins,
configured to run under the `topo` job in 15 minute intervals. This job will
collect switch forwarding tables (CAM), STP blocking status, CDP (Cisco
Discovery Protocol) neighbor information and also LLDP (Link Layer Discovery
Protocol) neighbor information.

The navtopology program will now prefer LLDP source information over CDP and
CDP source information over CAM source information when building NAV's
topology.

Unrecognized neighbors from CDP or LLDP are _not_ stored yet by NAV 3.11.0,
but this will be reimplemented in the 3.11 series.


NAV 3.10
========

To see the overview of scheduled features and reported bugs on the 3.10 series
of NAV, please go to https://launchpad.net/nav/3.10 .

Cricket configuration changes
-----------------------------

NAV 3.10 now configures Cricket to collect a wide range of available sensor
data from devices, including temperature sensors. Devices that implement
either ENTITY-SENSOR-MIB (RFC 3433), CISCO-ENVMON-MIB or IT-WATCHDOGS-MIB (IT
Watchdogs WeatherGoose) are supported.

Your need to copy the baseline Cricket configuration for sensors to your
cricket-config directory. Given that your NAV install prefix is
`/usr/local/nav/`::

  sudo cp -r doc/cricket/cricket-config/sensors \
             /usr/local/nav/etc/cricket-config/

You also need to add the `/sensors` tree to your Cricket's `subtree-sets`
file. See the example file containing all NAV subtrees at
`doc/cricket/cricket/subtree-sets`.

Topology detection
------------------

VLAN subtopology detection has now also been rewritten as a separate option to
the `navtopology` program. The old `networkDiscovery` service has been renamed
to `topology` and now runs physical and vlan topology detection using
`navtopology` once an hour.

If you notice topology problems that weren't there before the upgrade to 3.10,
please report them so that we can fix them.

The old detector code is deprecated, but if you wish to temporarily go back
to the old detector code, you can; see the comments in the `cron.d/topology`
file. The old detector will be removed entirely in NAV 3.11.


Link state monitoring
---------------------

ipdevpoll will now post `linkState` events when a port's link state changes,
regardless of whether you have configured your devices to send link state
traps to NAV.

To avoid a deluge of `linkDown` or `linkUp` alerts from all access ports in
your network, it is recommended to keep the `filter` setting in the
`[linkstate]` section of `ipdevpoll.conf` to the default setting of
`topology`. This means that events will only be posted for ports that have
been detected as uplinks or downlinks.

To facilitate faster detection of link state changes, ipdevpoll is now
configured with a `linkcheck` job that runs the `linkstate` plugin every five
minutes. You can adjust this to your own liking in `ipdevpoll.conf`.

SNMP agent monitoring
---------------------

An `snmpAgentDown` alert will now be sent if an IP device with a configured
community stops responding to SNMP requests.  The ipdevpoll job `snmpcheck`
will check for this every 30 minutes.

To receive alerts about SNMP agent states, please subscribe to
`snmpAgentState` events in your alert profile.


Redundant power supply and fan state monitoring
-----------------------------------------------

NAV now finds and stores information about power supply and fan units from
Cisco and HP devices, and monitors for any failures in redundant
configurations.

For the time being, the monitoring is run by a separate program,
`powersupplywatch.py`, which is by default set up to run as a cron job once an
hour. To adjust the monitoring interval, edit `cron.d/psuwatch`.


IPv6 status monitoring
----------------------

pping has gained support for pinging IPv6 hosts. _However_, SNMP over IPv6 is
not supported quite yet. This means you can add servers with IPv6 addresses
using SeedDB, but not with an enabled SNMP community.

Files to remove
---------------

If any of the following files and directories are still in your installation
after upgrading to NAV 3.10, they should be removed (installation prefix has
been stripped from these file names).  If you installed and upgraded NAV using
a packaging system, you should be able to safely ignore this section::

  doc/sql/*.sql
  etc/cron.d/networkDiscovery
  lib/python/nav/database.py
  lib/python/nav/mcc/routers.py
  lib/python/nav/mcc/switches.py
  lib/python/nav/web/templates/seeddbTemplate.py
  lib/python/nav/web/templates/selectTreeTemplate.py
  lib/python/nav/web/l2trace.py
  lib/python/nav/web/sortedStats.py
  lib/python/nav/web/netmap/handler.py
  lib/python/nav/web/serviceHelper.py
  lib/python/nav/web/ldapAuth.py
  lib/python/nav/web/selectTree.py
  lib/python/nav/statemon/output.py
  lib/templates/geomap/geomap-data-kml.xml
  apache/
  bin/navschema.py


NAV 3.9
=======

To see the overview of scheduled features and reported bugs on the 3.9 series
of NAV, please go to https://launchpad.net/nav/3.9 .


Dependency changes
------------------

- A dependency to the Python library NetworkX (http://networkx.lanl.gov/),
  version 1.0 or newer, has been introduced in the new topology
  detector.

  NetworkX lists a number of optional third party packages that will extend
  NetworkX' functionality, but none of these are currently needed by NAV.

- An optional, but recommended, dependency to the `pynetsnmp` library has been
  introduced to increase SNMP-related performance in the `ipdevpoll` daemon.
  `pynetsnmp` is a ctypes binding (as opposed to a native C module) enabling
  integration with the efficient SNMP processing of the mature NetSNMP
  library.

  `pynetsnmp` was created for and is distributed with ZenOSS.  There doesn't
  seem to be a separate tarball for `pynetsnmp`, but the source code
  repository is at http://dev.zenoss.com/trac/browser/trunk/pynetsnmp . The
  library has been packaged for Debian under the name `python-pynetsnmp`.



NAV 3.8
=======

Source code directory layout
----------------------------
The source code directory layout has changed.  All subystems in the
`subsystems` directory were merged in several top-level directories:

`python`
  All the Python libraries have moved here.

`java`
  All the Java code has moved here.

`bin`
  All executables have been moved here.

`etc`
  All initial/example configuration files have been moved here.

`media`
  All static media files to be served by Apache have moved here.

`templates`
  All Django templates used by NAV have moved here.

`sql`
  All the database schema initialization/migration related files have moved
  here.


Apache configuration
--------------------
NAV's preferred way of configuring Apache has changed.  The default target
directory for an Apache DocumentRoot has therefore also changed, to
`${prefix}/share/htdocs`.

NAV 3.8 only installs static media files into this directory - all Python code
is now kept in NAV's Python library directory.  For Cricket integration,
Cricket's CGI scripts and static media should still be installed in the
DocumentRoot under a separate `cricket` directory (or aliased to the /cricket
location).

NAV now provides its own basic Apache configuration file to be included in
your VirtualHost setup.  This file is installed as
`${sysconfdir}/apache/apache.conf`.  See the `Configuring Apache` section in
the INSTALL file for more details.


Database installation and migration
-----------------------------------
NAV 3.8 introduces an automatic database schema upgrade program.  Every time
you upgrade NAV, all you need to do to ensure your database schema is updated
is to run the `sql/syncdb.py` program.

This program will use the settings from `db.conf` to connect to the NAV
database.  It can also be used to create a NAV database from scratch.


PortAdmin
---------

NAV can now configure switch port descriptions and native VLANs from the IP
Device Info tool, provided that you have set an SNMP write community in
SeedDB (which is also necessary for the Arnold tool to work).

This functionality supports Cisco devices through proprietary MIBs.  Devices
from other vendors are supported as long as they properly implement the
Q-BRIDGE-MIB (RFC 2674) - This has been successfully tested on HP switches.
Alcatel switches seem to block write access to the necessary Q-BRIDGE objects;
we are still looking into this.

Please do not forget to secure your SNMP v2c communications using best
practices.  Limit SNMP communication with your devices to only the necessary
IP addresses or ranges using access lists or similar techniques.  You don't
want users on your network to sniff SNMP community strings and start
configuring your devices, do you?


Dependency changes
------------------

The INSTALL file used to refer to the python package `egenix-mxdatetime` as a
dependency.  This has been removed, as NAV stopped using it in version 3.6.
You psycopg2 installation may still require it, though.

NAV 3.8 also adds a dependency to the Python library `simplejson`.

Also, don't forget: The following dependencies changed from version 3.6 to
3.7:

* Python >= 2.5.0
* PostgreSQL >= 8.3
