External authentication (LDAP, REMOTE_USER)
===========================================

By default, users and passwords are created and stored locally on the NAV
instance. NAV also supports authenticating users via an external
service. The external methods NAV currently supports is authenticating with
LDAP, and authenticating against the header REMOTE_USER, set by the web server.

.. toctree::
   :maxdepth: 1

   ldap
   web_authentication
