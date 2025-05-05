===================================================================================================================
Authenticating with the apache plugin `mod_auth_openidc <https://github.com/zmartzone/mod_auth_openidc>`_ and Feide
===================================================================================================================

Enabling the plugin on Debian
=============================

First check if the plugin is already installed and enabled::

    $ sudo apache2ctl -M | grep openid
      auth_openidc_module (shared)

If it is, go straight to :ref:`configuration <openidc_feide_howto_configuration>`.

If not:

Install the plugin::

    $ sudo apt install libapache2-mod-auth-openidc

This should create the following files::

    /etc/apache2/mods-available/auth_openidc.conf
    /etc/apache2/mods-available/auth_openidc.load
    /etc/apache2/mods-enabled/auth_openidc.conf
    /etc/apache2/mods-enabled/auth_openidc.load

Enable with::

    $ sudo a2enmod auth_openidc

Disable with::

    $ sudo a2dismod auth_openidc


.. _openidc_feide_howto_configuration:
Feide Kundeportal configuration
===============================

You will need to ask somebody with the correct access-rights at `Feide
kundeportal <https://kunde.feide.no>`_ for your organization to create an
OpenID Connect-configuration. Configurations are locked to a specific NAV
domain name and user group and cannot be shared. If the domainname is updated
the Feide and Apache2-configurations will need to be updated as well.

The Feide admin will need:

* A name for configuration, we recommend: "NAV: domainname" or "NAV: your organization".
* An url to redirect to after login, this is the domainname followed by
  a relative url that is *not served by NAV*. We use ``/oidc`` in this howto.

Also, the ``userid-feide`` scope needs to be turned on at
*User information > Personal information*.

Apache2 Configuration
=====================

Apache virtual host configuration::

    <Location />
        .
        .

        AuthType openid-connect
        Require valid-user
    </Location>

    <Location /oidc>
        SetHandler none
        AuthType openid-connect
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

    OIDCProviderMetadataURL https://auth.dataporten.no/.well-known/openid-configuration
    OIDCClientID SOME-UUID
    OIDCClientSecret SOME-OTHER-UUID
    OIDCRedirectURI https://DOMAINNAME/oidc/
    OIDCCryptoPassphrase LONGRANDOMSTRING
    OIDCRemoteUserClaim https://n.feide.no/claims/eduPersonPrincipalName
    OIDCScope "openid userid-feide"

Note the location block ``<Location />``. The "Require"-line replaces any other
"requires" already there. This locks down the entire site. We haven't found
a way with this plugin to do it any other way.

The second location block (``<Location /oidc>``) just needs to be a relative
url that is not in use by anything else, this is used by the plugin as its
endpoint.

The third location block (``<Location /index/logout>``) is the url the plugin
redirects to after logout.

The remaining location blocks are either public urls (``/doc``, ``/about``),
parts of NAV that has its own authentication system (``/api``), or must not be
under the control of the plugin for the web frontend to correctly function
(``/refresh_session``). If you have added extra pages or apps to the nav-server
that will not use the NAV auth system you need to mark their urls similarly.

```OIDCClientID`` needs to be set to the fixed generated *client id*, while
``OIDCClientSecret`` needs to be set to the changeable ``client secret``. Both
are to be found in `Feide Kundeportal <https://kunde.feide.no>`_.

``OIDCRedirectURI`` is the domain name of the NAV instance as a URI, suffixed
with the plugin's magic endpoint url, in this case ``/oidc/``. This url needs
to be registered at the Feide dashboard as a redirect URI under
*Redirect URI after login*.

``OIDCCryptoPassphrase`` is used as a seed and should be kept secret.

``OIDCOAuthRemoteUserClaim`` is what information will be used as the username.
The exact claim may change.

``OIDCScope`` must at minimum contain ``"openid userid-feide"``, remember the
quotes.

NAV configuration
=================

``webfront.conf``::

    [remote-user]
    enabled = yes
    varname = REMOTE_USER
    logout-url = /oidc/?logout=
    workaround = feide-oidc
    autocreate = off

"oidc" in the ``logout-url`` points to the same place as the
``<Location /oidc>``-block in the apache configuration and the redirect URI in
the Feide dashboard.

By toggling autocreate to "on", users are automatically created on first login
via OIDC. This is probably not what you want, which is why the default is
"off". With it "off" it is necessary to pre-create the users in order to allow
login.

Gotchas
=======

When this is in use, local users like "admin" will no longer be available. Therefore, either:

* *before* enabling the plugin create a user that will use OIDC to login then
  set that user as admin
* *after* enabling the plugin set a user as admin via the CLI user script, ``navuser``
