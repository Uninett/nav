Network Administration Visualized list of authors
=================================================

This file tries to list everyone that has contributed to NAV, in the
form of code, documentation or packaging.

Currently active contributors/maintainers
-----------------------------------------

* Morten Brekkevold (formerly Vold) <morten.brekkevold at sikt.no>
  NAV's lead developer. Joined in 2002 to make NAV useable outside of NTNU.  Has
  been hacking and improving bits and pieces of NAV ever since.

* Hanne Moa <hanne.moa at sikt.no>
  Joined in 2017. An experienced Python developer who contributied the audit
  logging code, and has put down many hours in migrating to Python 3 and modern
  Django versions.

* Johanna England <johanna.england at sikt.no>
  Joined in 2021. Currently hacking away at open issues and learning the NAV
  codebase.

* Simon Oliver Tveit <simon.tveit at sikt.no>
  Joined in 2021. Currently hacking away at open issues and learning the NAV
  codebase.

* Ilona Podliashanyk <ilona.podliashanyk at sikt.no>
  Joined in 2022, working mainly as a front-end developer. Currently hacking
  away at open issues and learning the NAV codebase.

* Jørund Hellebø <jorund.hellebo at sikt.no>
  Joined part-time in 2024, working on DHCP statistics integration and building
  HTTP/REST API management profiles for Palo Alto API implementations, among
  other things.

* Simen Abelsen <simen.abelsen at sikt.no>
  Joined in August 2025, working on cleanup and modernization of the front-end
  codebase.

Other contributors and previous maintainers
-------------------------------------------
* Vidar Faltinsen <vidar.faltinsen at sikt.no>
  Founded the project in 1999.  He doesn't code, but he knows his way
  around a network, and has been a NAV mentor for all these years -
  producing documentation and offering keen insight into the problem
  domain.

* John-Magne Bredal
  Joined in 2000, and was instrumental in anything related to end user
  detentions (Arnold), the web interface and the API.

* Sigmund Augdal
  Active from 2017, until he left Uninett in 2019. An experienced Python
  developer who, among other things, rewrote the ipdevpoll multiprocess mode.

* Paulo Pamplona <paulo at nordu.net>
  Works at SUNET. Contributed a bugfix to strip null-bytes from bytestrings being
  made safe for PostgreSQL.

* Joar Heimonen <contact at joar.me>
  Contributed Palo Alto ARP plugin to enable ipdevpoll fetch ARP data from Palo
  Alto firewalls.

* Ragnhild Bodsberg
  Contributed various bugfixes to NAV as an intern at Sikt, during the summer
  of 2022.

* Philipp Petermann <philipp.petermann at unibas.ch>
  Contributed support for enabling CDP when configuring Cisco Voice VLANs in
  PortAdmin.

* Leigh Murray <l.d.murray@usit.uio.no>
  Implemented group-based ipdevpoll and pping, allowing multiple
  instances to run simultaneously handling specific groups of devices.

* Ruben Andreassen (University of Tromsø)
  Contributed the initial support for IT-WATCHDOGS-V4-MIB, GEIST-V4-MIB and
  PowerTek PDUs (PWTv1-MIB).

* Bård Schjander Flugon <bflugon at gmail.com>
  During his internship at Uninett, he wrote support for pluggable NAVbar
  search providers, consolidated a new SQL schema baseline from several years
  of migration scripts, and contributed multiple other improvements to NAV.

* Emil Henry Flakk <emil.flakk at sikt.no>
  Wrote the IPAM tool introduced in NAV 4.6, and continues to work on
  Netmap/Geomap fixes, among other things.

* Pär Stolpe <par at stolpe.se>
  Contributed more flexible LDAP authentication for Microsoft AD servers.

* Christian Strand Young <christian at strandyoung.com>
  Joined in the summer of 2011.  His main contributions are implementing IPv6
  support in pping and asynchronous DNS lookups in ipdevinfo & the Machine
  Tracker, as well as fixing various bugs.

* Christine Anne Sætre <christine.satre at ntnu.no>
  Interaction designer, hired as a consultant from NTNU to give feedback on UX
  during the NAV 4.0 interface redesign process.

* Morten Werner Forsbring <werner at debian.org>
  Packaging NAV for Debian 2004-2013.

* Roy Sindre Norangshol <roy.sindre.norangshol at sikt.no>
  Rewrote Netmap from a Java applet to a JavaScript implementation based on
  D3.js. Wrote the tools scripts for building NAV virtual machines based on
  Vagrant, and contributed to improve our automated JavaScript testing.

* Eivind Lysne <eivindlysne at gmail.com>
  Rewrote the remaining Cheetah templates to Django templates during the
  summer of 2013. Also contributed to the design changes scheduled for NAV
  4.0.

* Trond Kandal <trond.kandal at ntnu.no>
  Wrote PortAdmin with John-Magne.

* Ole Martin Bjørndalen <ole.martin.bjorndalen at uit.no>
  Wrote the MailIn system based on a Perl implementation from Uninett, and
  periodically contributes to the service monitor.

* Kai Arne Bjørnenak <kai.bjornenak at cc.uit.no>
  Write radius accounting logger.

* Magnus Motzfeldt Eide
  Active 2008-2012. Rewrote the old PHP-based Alert Profiles interface in
  Python/Django.  General code maintenance and rewrites of mod_python based
  systems to Django, and was also involved in the early development of
  ipdevpoll.

* Marius Halden <marius.halden at gmail.com>

* Matej Gregr <igregr at fit.vutbr.cz>

* Fredrik Skolmli
  Active 2010.  Contributed bugfixes and started the threshold configuration
  UI.

* Thomas Adamcik
  Active 2008-2010.  Rewrote the Perl-based Alert Engine in Python.
  Also rewrote the user admin panel to a Django-based solution, and contributed
  much to enable continuous integration using Hudson.

* Jørgen Abrahamsen
  Active 2008-2010. Bugfixes and features to various parts of NAV, such as
  report, smsd and ipdevinfo.

* Kristian Klette
  Active 2007-2010.  Wrote Netmap and the rewritten Network Explorer.

* Øystein Skartsæterhagen <oysteini at pvv.ntnu.no>, 2009
  Wrote Geomap, the OpenStreetMap-based traffic map.

* Roger Kristiansen

* Stein Magnus Jodal,  2006-2008
  Rewrote the SMS daemon from Perl to Python for NAV 3.2.  During the
  next couple of series releases, he cleaned up the entire web
  interface, defined new policies for how to code web interfaces in
  NAV, and rewrote several web tools.  Introduced Django to NAV 3.5,
  using it to rewrite the creaky IP Device Browser to the IP Device
  Info tool.

* Erlend Midttun <erlend.midttun at ntnu.no>

* Jostein Gogstad <jostein.gogstad at idi.ntnu.no>
  2007, implemented support for collecting IPv6 prefixes and
  neighboring caches, and matrix display of IPv6 subnets.

* Kristian Eide <kreide at gmail.com>
  Active 2000-2005.  Wrote the first Traffic Map applet.  Instrumental
  in the redesign of NAV for version 3, for which he wrote the
  getDeviceData SNMP collection engine, the camlogger, the event
  engine, the topology discovery mechanisms and the network explorer
  and l2trace web tools.

* Gro-Anita Vindheim <gro-anita.vindheim at ntnu.no>
  Active 1999-2001 and 2003-2005.  Wrote live.pl, the original pinger,
  and several other parts of NAV 2.  Maintenance on SQL reports, NAV
  v2->v3 migration helper scripts.

* Magnar Sveen, 2003-2004
  Designed the new web interface for NAV 3 and wrote much of the
  surrounding toolbox and user preferences code.

* Hans Jørgen Hoel, 2003-2004
  Wrote the SeedDB (formerly EditDB) and the original Device
  Management web tools. Partly involved in event engine's handling of
  device lifecycle events.

* Arne Øslebø
  Active 2002-2004.  Wrote the first Alert Engine in Perl.

* Andreas Åkre Solberg <andreas.solberg at sikt.no>
  Active 2002-2004.  Wrote the first Alert Profiles web interface in
  PHP, and parts of the first Alert Engine.

This dynamic duo wrote most of NAV's service monitor and parallel
pinger:

* Stian Søiland, 2002-2004
* Magnus Thanem Nordseth, 2002-2006

* Sigurd Gartmann, 2001-2004
  Wrote the SNMP collector for NAV 2, the report system and the syslog
  analyzer.

* Arve Vanvik, 2004
  Oracle plugin for the service monitor.

* Erlend Mjåvatten, 2003
  Wrote the original rrd browser and supporting libraries.

* Bjørn Ove Grøtan, 2003
  Wrote the original message&maintenance (emotd) web tool, and
  contributed initial code for LDAP authentication.

* Daniel Sandvold, 2002

* Erik Gorset, 2002
  Wrote parts of the service monitor and parallel pinger.

* Knut-Helge Vindheim <knut-helge.vindheim at ntnu.no>, 1999-2002
  Maintenance on various NAV 2 parts: The SMS daemon, SNMP collection
  scripts, database backup system.  For the most part, Knut-Helge has
  contributed invaluable insights into the operation of a large campus
  network.

* Trygve Lunheim, 1999-2000
  The original introduction of MRTG/Cricket integration.

* Stig Venås, 1999
  Wrote the original arp cache collector (arplogger.pl), which
  remained mostly unchanged in NAV for 9 years.

These guys were involved in projects that were precursors to NAV (such as the
first attempt at building a topology graph):

* Eric Sandnes, 1999
* Tor-Arne Kvaløy, 1999
