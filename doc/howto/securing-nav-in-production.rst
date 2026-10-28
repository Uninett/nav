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

Running NAV behind a TLS-terminating reverse proxy
--------------------------------------------------

If NAV is served exclusively through a reverse proxy that terminates SSL/TLS
(e.g. HAProxy or nginx), and the proxy forwards requests to NAV as plain HTTP,
set ``proxy_tls_terminated`` to ``yes``. NAV will then trust the
``X-Forwarded-Proto`` header sent by the proxy to tell whether the client's
original request used HTTPS. This makes Django's CSRF protection accept logins
and other form submissions, and makes the absolute URLs that NAV generates
(such as OAuth/OpenID Connect callback URLs and QR codes) use ``https://``.

For this to be safe, all of the following must hold:

* The proxy must send ``X-Forwarded-Proto: https`` on requests it received over
  HTTPS.
* The proxy must *overwrite* any ``X-Forwarded-Proto`` header sent by the
  client, never pass it through or append to it.
* NAV must not be reachable except through the proxy. Otherwise, any client
  can claim to be using HTTPS.

You still need ``needs_tls = yes`` to enable secure cookies.

As an example, an nginx configuration serving NAV through uWSGI could look
like this::

    location / {
        include uwsgi_params;
        uwsgi_param HTTP_X_FORWARDED_PROTO $scheme;
        uwsgi_pass 127.0.0.1:7900;
    }

``csrf_trusted_origins`` is a space-separated list of additional origins
(``scheme://host[:port]``, without a path) that NAV should accept form
submissions from, e.g. ``https://nav.example.org https://nav-alias.example.org``.
Django's CSRF protection compares the ``Origin`` header sent by the browser
with the scheme and ``Host`` header of the request that NAV receives. You only
need this option if these differ from the public address your users access NAV
by, e.g. if your reverse proxy rewrites the ``Host`` header.
