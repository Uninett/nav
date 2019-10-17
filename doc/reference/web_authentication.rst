=========================================
External web authentication (REMOTE_USER)
=========================================

Whether external authentication (via the ``REMOTE_USER`` http header) is
honored is configured in ``webfront.conf``. In the section ``[remote-user]``,
set ``enabled`` to ``on`` or ``yes``. (A missing section or value is
interpreted as the support being off.) When enabled, NAV will check for the
HTTP header in ``varname``, "REMOTE_USER" by default, on every page load. if
there is a string there, NAV will attempt to use it as a username to log in
with. An account will be created if one does not already exist for that
username.

``REMOTE_USER`` or another header can be set by the web server hosting NAV,
and is a simple way of supporting federated logins via eg. Kerberors or SAML,
provided the web server has the necessary support/modules/plugins.

If the value set in the header is not sufficiently username-like, it can be
converted via a workaround as set in the ``workaround`` header. The only
workaround supported so far is for Feide via OpenId Connect, and you turn this
on by adding ``workaround = feide-oidc`` in the config.

Since the password is controlled from a system externally to NAV, the user does
not have access to change the password from inside NAV. If an account is set to
invalid in NAV, the user will not be logged in, even if the header is set.

Relevant How To:

.. toctree::

  ../howto/mod_auth_openidc_feide
