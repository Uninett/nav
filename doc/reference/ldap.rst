=======================================
Configuring NAV for LDAP authentication
=======================================

NAV can authenticate web users externally via an LDAP server.  This
article describes how this feature works, and how to configure it.

Configurable options
====================

Configuration for LDAP authentication is stored in the config file
:file:`webfront/webfront.conf`, in the ``[ldap]`` section.  You should restart
Apache to make sure any config changes take effect.

Available options:

**enabled**
  Set to `yes` to enable LDAP authentication.

**server**
  IP address or hostname of your LDAP server.

**port**
  The port your LDAP server listens to. The default is 389 for unencrypted and
  TLS encrypted sessions. SSL encrypted LDAP is usually on port 636.

**encryption**
  `tls`, `ssl` or `none`

**uid_attr**
  The name of the attribute that uniquely identifies each user object (RDN in
  LDAP-speak). The value of this attribute will be the login name in NAV. The
  default setting is `uid`.

**name_attr**
  The name of the attribute that contains a user's full real name.  The
  default setting is `cn`.

**basedn**
  The root DN of your user objects.

**require_group**
  The DN of a group object, in which membership is required for a user to be
  allowed to log in to NAV.  Its objectClass should be one of `groupOfNames`,
  `groupOfUniqueNames` or `posixGroup`.

**group_search**
  .. versionadded:: 4.4

  Can be used to customize the search filter used when verifying group
  memberships using the `require_group` option (specifically for group schemas
  that register user distinguished names as member values).

  The default value, ``(member=%%s)`` is fine for most purposes. Microsoft AD
  will support a recursive group search operator, so that nested group
  memberships are allowed. Use a value of
  ``(member:1.2.840.113556.1.4.1941:=%%s)`` to enable this AD extension

**require_entitlement**
  .. versionadded:: 4.9.6

  A string defining the name of an entitlement that the user object must have
  in order for the user to be allowed to log in to NAV.

**admin_entitlement**
  .. versionadded:: 4.9.7

  If a user object has this entitlement, the user will be granted membership
  in the NAV Administrators group. If the user object does not have this
  entitlement, the user will be stripped of their Administrator privileges. If
  unset, nothing happens.

**entitlement_attribute**
  .. versionadded:: 4.9.6

  Can be used to customize the user object attribute used to verify entitlements.
  The default value is ``eduPersonEntitlement``.

**lookupmethod**
  .. versionadded:: 3.7

  Selects which method to use for finding users in the LDAP directory. Valid
  settings are `direct` and `search`. `direct` will cause the user's DN to be
  constructed as ``<uid_attr>=<login name>,<basedn>``. Specifying `search`
  will bind to the LDAP directory as `<manager>`, if specified, and search for
  ``<uid_attr>=<login name>``. If a bind `suffix` is specified for AD-style
  binds, using a manager account can be avoided.

**suffix**
  .. versionadded:: 4.4

  When set to a doman suffix, such as ``@ad.example.com``, the username to
  bind as will be constructed from the login name and this suffix. This type
  of direct bind is supported by Microsoft AD, and can be used to avoid having
  to configure a manager user to search the catalog.

**manager**
  .. versionadded:: 3.7

  The DN of a user to bind as when searching for users in the directory. Can
  be omitted if authentication is not required for searches, or the
  `lookupmethod` is `direct`.

**managerpassword**
  .. versionadded:: 3.7

  Password needed to bind as the `manager` user.

**encoding**
  .. versionadded:: 3.15

  Specifies the character encoding to expect from the LDAP catalog. The
  default value is UTF-8.

**debug**
  Set to `yes` to have the OpenLDAP library output debug information to
  stderr.  This will usually end up in the Apache error logs.


Example config
--------------

A typical setup for an OpenLDAP server looks like this:

.. code-block:: ini

  [ldap]
  enabled = yes
  server = ldap.example.com
  port=389
  basedn= ou=people,dc=example,dc=com
  require_group= cn=noc-operators,cn=groups,dc=example,dc=com

A typical setup for Microsoft Active Directory would look more like this:

.. code-block:: ini

  [ldap]
  enabled = yes
  server = ad.example.com
  port = 636
  encryption = ssl

  uid_attr = sAMAccountName
  basedn = ou=people,dc=example,dc=com
  lookupmethod = search
  manager = cn=John Doe,ou=people,dc=example,dc=com
  managerpassword = secret

Or, without a manager account, like this:

.. code-block:: ini

  [ldap]
  enabled = yes
  server = ad.example.com
  port = 636
  encryption = ssl

  uid_attr = sAMAccountName
  basedn = ou=people,dc=example,dc=com
  suffix = @ad.example.com
  lookupmethod = search


Certificates
------------

If you are using TLS or SSL encryption with your LDAP server, you may need to
configure your OpenLDAP installation with the proper certificates.  On most
systems, you should see the man page :manpage:`ldap.conf(5)` for details.  On
Debian, this config file is located in :file:`/etc/ldap/`.

If you are using a self-signed certificate, you should put that certificate
(in *pem* format) somewhere accessible on your NAV server, and add the
`TLS_CACERT` option to :file:`ldap.conf`::

  TLS_CACERT     /path/to/my/certificate.pem


How it works
============

When LDAP authentication is enabled, NAV will, if necessary, attempt
to do authenticated binds against the LDAP tree when users log in.

**When the user is created locally by the admin**

* NAV performs a regular password authentication against the local NAVdb. LDAP
  is not used.

**When the user does not exist in the local NAVdb**

* NAV attempts to authenticate the user with LDAP, according to its config.
* If successful, it creates a local account in NAVdb for this user. The user's
  full name is retrieved from LDAP, and a salted hashed copy of the password
  is stored in the database.D
* If unsuccessful, the login attempt is rejected.
* If the LDAP server did not answer, the login attempt is rejected, and an
  LDAP error is displayed.

**When the user exists in the local NAVdb, and has previously been retrieved from the LDAP server**

* NAV attempts to authenticate the user with LDAP, according to its config.
* If successful, it updates the local account in NAVdb with the user's
  full name and a hashed copy of the supplied password.
* If unsuccessful, the login attempt is rejected.
* If the LDAP server did not answer, NAV falls back to local
  authentication against the hashed password copy in NAVdb.

Users should always be able to login to NAV to diagnose network problems, even
if the LDAP server happens to be unreachable (this could be the very problem
you want to inspect).  The above documented authentication procedure makes
sure that any user known to NAV will be able to log in as long as NAV is up.
LDAP-based users that have never logged in to NAV before will not be able to
do so as long as the LDAP server is unreachable.

Authenticating existing NAV accounts with LDAP
==============================================

Users that have been created locally in NAV will not be authenticated with the
LDAP server when LDAP authentication is enabled at a later time.  The only way
to do this is to tinker with the SQL database.

Run :code:`psql nav nav`, use the password from :file:`db.conf`.  List the
existing accounts::

  nav=# select * from account;
    id  |  login  |       name        | password | ext_sync
  ------+---------+-------------------+----------+----------
      0 | default | Default User      |          |
      1 | admin   | NAV Administrator | password |
   1000 | foo     | Foo Bar           | password |
   1001 | arthur  | A. Dent           | password |
   1002 | zaphod  | Z. Beeblebrox     | password | ldap
  (5 rows)

The `ext_sync` column defines what external mechanism is used to authenticate
a user.  As you can see, only the user *zaphod* will be authenticated using
LDAP here.  To allow the user *arthur* to be authenticated using LDAP
(assuming the LDAP server knows of a user with that login name), issue the
following SQL statement:

.. code-block:: sql

  UPDATE account SET ext_sync='ldap' WHERE login='arthur';
