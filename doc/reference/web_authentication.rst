================================
Web authentication (REMOTE_USER)
================================

If you set ``AUTH_SUPPORT_REMOTE_USER`` to ``True`` in ``nav.conf``, NAV will
check for the HTTP header ``REMOTE_USER`` on every page load, and attempt to
log in the username found there. An account will be created if one does not
already exist for that username.

``REMOTE_USER`` can be set by the web server hosting NAV, and is a simple way
of supporting federated logins via eg. Kerberors or SAML, provided the web
server has the necessary support/modules/plugins.

Since the password is controlled from a system externally to NAV, the user does
not have access to change the password from inside NAV. If an account is set to
invalid in NAV, the user will not be logged in, even if the header is set.
