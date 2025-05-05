================================================================================================================
Authenticating with the apache plugin `mod_auth_mellon <https://github.com/latchset/mod_auth_mellon>`_ and Feide
================================================================================================================

Highly recommended: turn on debug logging while setting things up!

In ``/etc/nav/logging.conf`` in the section ``[levels]``, set ``nav.web.auth``
to ``DEBUG``. The relevant log to keep an eye on will depend on how apache2 is
running NAV, if it's using ``uwsgi`` the file is probably
``/var/log/uwsgi/nav/nav.log``.

Enabling the plugin on Debian
=============================

First check if the plugin is already installed and enabled::

    $ sudo apache2ctl -M | grep mellon
      auth_mellon_module (shared)

If it is, go straight to :ref:`configuration <mellon_feide_howto_configuration>`.

If not:

Install the plugin::

            $ sudo apt install libapache2-mod-auth-mellon

This should create the following files::

    /etc/apache2/mods-available/auth_mellon.conf
    /etc/apache2/mods-available/auth_mellon.load
    /etc/apache2/mods-enabled/auth_mellon.conf
    /etc/apache2/mods-enabled/auth_mellon.load

Enable with::

    $ sudo a2enmod auth_mellon

Disable with::

    $ sudo a2dismod auth_mellon

.. _mellon_feide_howto_configuration:
Files needed
============

Make a directory ``/etc/apache2/mellon`` on the NAV host. This will contain the
keys, certificates and metadata.

You need to download the idp metadata.

* `Test metadata <https://idp-test.feide.no/simplesaml/saml2/idp/metadata.php>`_
* `Production metadata <https://idp.feide.no/simplesaml/saml2/idp/metadata.php>`_

Save the file as ``/etc/apache2/mellon/idp-metadata.xml``.

The easiest way to create the sp metadata is with the command
``mellon_create_metadata``. Stand in ``/etc/apache2/mellon`` and run::

    mellon_create_metadata https://DOMAINNAME https://DOMAINNAME/mellon

This will output a summary and create three files: ``https_DOMAINNAME.cert``,
``https_DOMAINNAME.key`` and ``https_DOMAINNAME.xml``. You can edit the
xml-file if needed.

Feide Kundeportal configuration
===============================

You will need to ask somebody with the correct access-rights at `Feide
kundeportal <https://kunde.feide.no>`_ for your organization to create
a service and a SAML 2.0 configuration for that service. Configurations are
locked to a specific NAV domain name and user group and cannot be shared. If
the domainname is updated the Feide and Apache2-configurations will need to be
updated as well.

The Feide admin will need:

* A name for the service, we recommend: "NAV: domainname" or "NAV: your organization".
* An url to redirect to after login, this is the domainname followed by
  a relative url that is *not served by NAV*. We use ``/mellon`` in this howto.
* A copy of ``https_DOMAINNAME.xml``, to use in the SP metadata field.

Also, the ``userid-feide`` scope needs to be turned on at
*User information > Personal information*.

Apache2 Configuration
=====================

Apache virtual host configuration::

    <Location />
        .
        .

        AuthType mellon
        Require valid-user

        MellonEnable "auth"
        MellonSecureCookie On
        MellonUser "eduPersonPrincipalName"
        MellonMergeEnvVars On
        #MellonSessionIdleTimeout 28800  # auto logout after 8 hours
        MellonSPMetadataFile /etc/apache2/mellon/https_DOMAINNAME.xml
        MellonSPPrivateKeyFile /etc/apache2/mellon/https_DOMAINNAME.key
        MellonSPCertFile /etc/apache2/mellon/https_DOMAINNAME.cert
        MellonIdPMetadataFile /etc/apache2/mellon/idp-metadata.xml
    </Location>

    <Location /mellon>
        SetHandler none
        AuthType mellon
        Require valid-user

    </Location>

    <Location /index/logout>
        AuthType None
        Require all granted
    </Location>

    <Location /about>
        AuthType None
        Require all granted
    </Location>

    <Location /refresh_session>
        AuthType None
        Require all granted
    </Location>

    <Location /api>
        AuthType None
        Require all granted
    </Location>

    <Location /doc>
        AuthType None
        Require all granted
    </Location>

Note the location block ``<Location />``. The "Require"-line replaces any other
"requires" already there. This locks down the entire site. We haven't found
a way with this plugin to do it any other way.

The second location block (``<Location /mellon>``) just needs to be a relative
url that is not in use by anything else, this is used by the plugin as its
endpoint.

The third location block (``<Location /index/logout>``) is the url that must be
visited before the plugin redirects to the IDP for logout.

The remaining location blocks are either public urls (``/doc``, ``/about``),
parts of NAV that has its own authentication system (``/api``), or must not be
under the control of the plugin for the web frontend to correctly function
(``/refresh_session``). If you have added extra pages or apps to the nav-server
that will not use the NAV auth system you need to mark their urls similarly.

Note that ``MellonSessionIdleTimeout`` has been commented out. Not all versions
of mod-auth-mellon support this configuration flag.

Restricting access by affiliation
---------------------------------

A Feide-user has one or more affiliations like "student", "employee" or "staff".
If it is necessary to restrict access by affiliation it is necessary to amend
the apache config file. Just below ``MellonMergeEnvVars`` add::

    MellonRequire "eduPersonAffiliation" "staff" "other_affiliation"

Provided debug-logging has been turned on you can see exactly which
affiliations are available. Look for a line containing
"MELLON_eduPersonAffiliation".

There must be one or more quoted strings after "eduPersonAffiliation".

NAV configuration
=================

``webfront.conf``::

    [remote-user]
    enabled = yes
    varname = REMOTE_USER
    post-logout-redirect-url = /mellon/logout?returnTo=/

"mellon" in the ``post-logout-redirect-url`` points to the same place as the
``<Location /mellon>``-block in the apache configuration. This is hardcoded in
the SP metadata as well.

Gotchas
=======

When this is in use, local users like "admin" will no longer be available.
Therefore, either:

* *before* enabling the plugin create a user that will use OIDC to login then
  set that user as admin
* *after* enabling the plugin set a user as admin via the CLI user script,
  ``navuser``
