===
FAQ
===

Frequently Asked Questions for NAV

Is vendor X / device Y supported?
---------------------------------

NAV supports any managed (SNMP v1 or v2c-enabled) routing and switching device
that implements the relevant, standard IETF MIB support.

Unfortunately, many vendors seem to eschew some of these important IETF MIBs
in favor of their own, proprietary SNMP MIB modules. NAV has adequate support
for proprietary MIBs from large vendors such as Cisco and Hewlett Packard, as
these have been a mainstay in the Norwegian higher education sector for years.

For any other vendors, we suggest that you just add your devices to NAV and
see whether NAV reports what you want it to report. If it doesn't, submit a
question to the mailing list, nav-users@lister.sikt.no.

Why are there gaps in my graphs?
--------------------------------

There are multiple possible sources for problems like this. Please read our
:doc:`guide to debugging choppy graph issues<graph_gaps>`.


Why does NAV list my device's uplink as *N/A*?
----------------------------------------------

This means that topology discovery has failed for some reason.

Uplinks/downlinks in NAV require VLAN topology detection to be completed, as
directionality of links is part of this information. NAV may have actually
found the neighboring device on your port just find, but is unable to detect
which VLANs are active on the link - since directionality information is
missing, NAV doesn't know whether the neighbor represents an uplink or a
downlink.

Please see our :doc:`guide for troubleshooting topology
</howto/debugging-topology>` for more information.

Why doesn't device X show as down in the status page when I know it's down?
---------------------------------------------------------------------------

First, browse the device in ipdevinfo (search for it by name or IP in the
NAVbar). Does it list as up or down here?

Has the device been placed on maintenance, or has the alert already been
acknowledged by someone else? Check your status filter.

Remember, the *event engine* holds back *boxDown* alerts for up to four
minutes (configurable in :file:`eventengine.conf`) while waiting for the
situation to resolve itself. While waiting for the recovery, the device may be
marked as down in its *ipdevinfo* page, without an actual alert having been
posted yet.

If things still seem to not work, ensure both :program:`pping` and
:program:`eventengine` are running, using the :code:`nav status` command. Then
check the logs of these programs to see whether they have detected the
situation. :file:`pping.log` should indicate whether pping has failed to get a
ping response from the device. :file:`eventengine.log` should indicate whether
the *event engine* has detected *pping*'s notice of this.

A device is down, I see it on the status page, my profile should cover the event, but I am not alerted. Why?
--------------------------------------------------------------------------------------------------------------

First, verify that the alert engine (:code:`nav status alertengine`) is
running. Use :file:`alertengine.log` to verify that alert engine processed
such an alert. Did it cover your user? If not, double check your active
profile. You may want to make a new profile that covers every alarm, to see if
you get any alerts then.


Why is my Cisco switch' syslog full of SNMP-3-AUTHFAIL messages for requests from my NAV server?
-------------------------------------------------------------------------------------------------

Because of what Cisco calls *community indexing*. A 802.1q-enabled Cisco
switch will maintain separate switching information MIB instances (BRIDGE-MIB)
for each active VLAN.

Querying for switching information for VLAN 20 requires NAV to modify the SNMP
community used for communicating with the switch. If the community is
``public``, NAV must use the community ``public@20``.

To obtain all entries from the forwarding tables of such a switch (i.e. in
order to facilitate NAV's machine tracking and topology functionality), or
just to know which interfaces are switch ports, NAV must know which VLANs are
actively forwarded by the switch. Sometimes, Cisco devices report active VLANs
that it doesn't have a BRIDGE-MIB instance for.

Unfortunately, if NAV tries to query a VLAN that has no BRIDGE-MIB instance,
the switch will log this as an SNMP authentication failure.

I added a new IP Device using SeedDB, but nothing happens. Why?
---------------------------------------------------------------

NAV's SNMP collector, :program:`ipdevpoll`, should notice the new IP Device
within 2 minutes. Be patient. If you're impatient, restart
:program:`ipdevpoll`, or check its log file, :file:`ipdevpoll.log`.

How do I make NAV send SMS alerts?
----------------------------------

NAV provides an :doc:`SMS daemon </reference/smsd>` to dispatch SMS alerts. The
daemon uses a plugin system to provide support for multiple methods of SMS
message dispatch. Examples include a dispatcher for a locally-attached GSM
device (using Gammu), a dispatcher for a simple email-to-SMS interface, a
dispatcher for simple REST-based web SMS API's. You could also write your own
plugin.

We've always recommended attaching a GSM device directly to your NAV server,
to ensure that you have an out-of-band way of being notified about network
problems. To do so, get a GSM device that's supported by `Gammu
<http://www.gammu.org/wiki/index.php?title=Gammu:Main_Page>`_.

We've found it's best to avoid handsets, as these are built to be exactly
that: Handsets. Sometimes, they require some form of user-interaction to
continue operating, which isn't always feasible in a datacenter. At Sikt,
we've had good results with GSM terminals from Siemens/Cinterion/Gemalto.


How long are ARP and CAM records kept in the database?
------------------------------------------------------

NAV stores ARP an CAM records **indefinitely**, making them available for
search in the :program:`Machine Tracker` web UI.

*However*, in some jurisdictions, this type of data is considered personally
identifiable and its retention is regulated by privacy laws. You may therefore
be required by law to remove old ARP and CAM records from your database.

The :program:`navclean` command line program can be used to delete old ARP and
CAM records from the database. Many users run a :program:`navclean` command
from their *crontabs* to clean out old ARP and CAM records, like in this
example::

  # m h  dom mon dow   command
  * 6 * * * navclean --force --arp --cam --interval '6 months'

See the output of ``navclean --help`` for usage details.

.. toctree::
    :hidden:

    /faq/graph_gaps
