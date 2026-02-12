Authentication
==============

By default, users and passwords are created and stored locally on the NAV
instance. It is possible to add in a second factor when authenticating (2FA/MFA).

NAV also supports authenticating users via an external
service. The external methods NAV currently supports is authenticating with
LDAP, and authenticating against the header REMOTE_USER, set by the web server.

.. toctree::
   :maxdepth: 1

   mfa
   ldap
   remote_user
