=========================================
External web authentication (REMOTE_USER)
=========================================

The NAV web UI can be made to honor the ``REMOTE_USER`` HTTP header as a means
of external authentication, by setting the appropriate options of the
``[remote-user]`` section of :file:`webfront.conf`.

The feature is enabled by setting ``enabled=yes`` in this section (A missing
section or value, or the value ``off`` is interpreted as the support being
off). When enabled, NAV will check for the HTTP header in ``varname`` (set to
``REMOTE_USER`` by default), on every page load. If there is a string there, NAV
will attempt to use it as a username to log in with. An account will be created
if one does not already exist for that username.

``REMOTE_USER`` (or another header) can be set by the web server hosting NAV,
and is a simple way of supporting federated logins via eg. Kerberors or SAML,
provided the web server has the necessary support/modules/plugins.

Since the password is controlled from a system externally to NAV, the user does
not have access to change the password from inside NAV. If an account is set to
invalid in NAV, the user will not be logged in, even if the header is set.

Creating users on first login
-----------------------------

Earlier versions of this functionality created users on first login. That is no
longer the case. To enable the previous behaviour, set ``autocreate = on`` in
the ``[remote-user]`` section in the config-file.

With the default, which is ``off``, it is necessary to pre-create users for
them to be able to log in. This can be done from the command line with
``navuser``, or via the web interface.

Workarounds for "strange" `REMOTE_USER` values
----------------------------------------------

If the value set in the header is not sufficiently username-like, it can be
converted via a workaround as set in the ``workaround`` header. The only
workaround supported so far is for Feide via OpenId Connect, and you turn this
on by adding ``workaround = feide-oidc`` in the config section.

Setting specific URLs for external login/logout mechanism
---------------------------------------------------------

If you want NAV to use the remote idP's URLs for logging in and/or out, you can
set the ``login-url`` and the ``logout-url`` options in the ``[remote-user]``
section. If the external mechanism supports redirecting the client back to the
originating site upon login/logout completion, the originating NAV URL can be
inserted using the placeholder string ``{}``.  Example::

    [remote-user]
    enabled = yes
    login-url = https://sso.example.org/login?nexthop={}
    logout-url = https://sso.example.org/logout?nexthop={}

``logout-url`` will set the link that the logout-button points to, the default
is "/index/logout".

Some remote user systems need to be visited *after* NAV has logged out the
user locally. The flag for that is ``post-logout-redirect-url``.


Relevant How Tos:
-----------------

* :doc:`../howto/mod_auth_openidc_feide`
