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

If your NAV server is exclusively behind a reverse proxy that terminates the SSL/TLS sessions
(e.g. HAProxy) so that the connections that go to the NAV server itself
are plain HTTP then ``proxy_tls_terminated`` should be set to ``yes``. This makes it so
the NAV server trusts that all connections were originally HTTPS.

``csrf_trusted_origins`` allows you to configure trusted origins for unsafe requests
as a space separated list. This can be used in conjunction with ``proxy_tls_terminated``.
If the server is behind a reverse proxy (so ``proxy_tls_terminated`` is set to ``yes``) then you can end
up with a mismatch between the origin header in requests (will be ``https://...`` assuming ``needs_tls`` is
set to ``yes``), but django will see the scheme as ``http://`` since that is what the reverse proxy
will use to send requests to the NAV server. This problem can be resolved by setting ``csrf_trusted_origins``
to be a list of the public facing URLs that you use to access NAV from outside the reverse proxy.
