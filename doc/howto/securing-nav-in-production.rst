==========================
Securing NAV in production
==========================

Overview
========

The default configuration of NAV is set up to work well during development, but
needs to be tightened when running in production.

NAV consists of pages controlled by NAV itself, and pages served directly by
the web server. Security features for NAV's own pages are controlled via the
``[security]``-section in the file :file:`webfront/webfront.conf`, while
security for the other pages are controlled directly by the web server.


SSL/TLS
=======

This needs to be turned on in the webserver itself. While there is no reason to
serve any of NAV without SSL/TLS turned off, it is especially important for the
pages controlled by NAV.

When the server serves NAV with SSL/TLS, ensure that the ``needs_tls``-flag in
the ``[security]``-section is set to ``yes``. This explicitly turns on secure
cookies, which is dependent on SSL being in use.
