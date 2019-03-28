=================================================
 Network Administration Visualized release notes
=================================================

Please report bugs at https://github.com/uninett/nav/issues/new . To browse
existing bug reports, go to https://github.com/uninett/nav/issues .

To see an overview of upcoming release milestones and the issues they resolve,
please go to https://github.com/uninett/nav/milestones .

NAV 4.10
========

Changed command line options
----------------------------

The ``--verify`` option has been removed from :program:`powersupplywatch.py`.
All logging settings are controlled in :file:`logging.conf`, as with any
other NAV program.

Dependency changes
------------------

Upgraded dependencies
~~~~~~~~~~~~~~~~~~~~~

The version requirements have changed for these dependencies:

* :mod:`feedparser` must be any version from the *5.2* series.
* :mod:`networkx` must be any version from the *2.2* series.
* :mod:`IPy` must be at least version *1.00*.
* :mod:`pynetsnmp-2` must be version *0.1.5*.


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
initializing the database from scratch, using the :option:`-c` option.
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
https://nav.uninett.no/doc/dev/howto/using_the_api.html . We know a lot of
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

    1. :kbd:`gpg -a --gen-random 1 51`
    2. :kbd:`makepasswd --chars 51`
    3. :kbd:`pwgen -s 51 1`

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
