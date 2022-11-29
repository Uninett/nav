======================================
Usage and notes for isc_dhcpd_graphite
======================================

This script needs python3.

For arguments, try::

        isc_dhcpd_graphite.py --help

The script runs ``dhcpd_pool`` (full path given with -C) with the flag
``-f j`` to make it emit json.

Building the prefix
===================

The dotted-path that graphite uses to store data is controlled by the prefix
argument to the script (-p), the optional location argument (-l) and what
``dhcpd_pool`` returns as its ``location`` key.

The default prefix is "nav.dhcp".

If ``-p`` is "nav.bloviate", ``-l`` is not set and the ``location`` in the json
is "vlan1" the resulting graphite path is ``nav.bloviate.vlan1``.


Assumptions about Location
--------------------------

The script assumes that the value of the ``location``-key contains a vlan-name
of the form "vlanNUMBER", regex ``vlan\d+``. If this is not the case, a warning
is issued on stderr and that row of results is not passed on to graphite.

The location-value is normalized so that a value of "Student vlan2 new" is sent
to graphite as "vlan2".
