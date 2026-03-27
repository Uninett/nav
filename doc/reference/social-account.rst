==========================================
External web authentication (OAuth2, OIDC)
==========================================

It is possible to log in to the NAV web UI with an external identity provider
like OAuth2 or OIDC with depending on the HTTP header ``REMOTE_USER``.

NAV uses the 3rd party django app ``django-allauth`` for this.

The configuration is stored in the file :file:`webfront/authentication.toml`.

.. note::
   See the howto :doc:`Authenticating with OIDC/OAuth2 by using a local
   settings file <../howto/allauth-and-oidc>` for the full power of allauth,
   but please do only one of the two: either ``webfront/authentication.toml``
   or a local settings file.

Support for SAML is planned.

Using a provider bundled with django-allauth
============================================

Have a look at the list of providers at `django-allauth's provider list
<https://docs.allauth.org/en/latest/socialaccount/providers/index.html>`_.

You will need the name of the module (for instance
``allauth.socialaccount.providers.github`` for GitHub), the provider id
(``github`` for GitHub, this is always a valid python module name) and at
minimum a ``client_id`` and a ``secret``.

Note that the bundled "openid" provider needs extra tables, NAV does not ship
with them by default.

Example: Logging in with the bundled GitHub provider
----------------------------------------------------

Anyone can get an account at GitHub so we're using that as the most basic
example.

See `Authorizing OAuth apps
<https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps,>`_
for details.

The app for this does not need any additional tables so the below configuration
is all you need.

.. code-block:: toml

   [social.providers.github
   module-path = "allauth.socialaccount.providers.github"
   client_id = "your.service.id"
   secret = "your.service.secret"

You need to create an OAuth app at `GitHub: New OAuth Application
<https://github.com/settings/applications/new>`_.

The client id and regenerating the secret will be available on `GitHub:
Authorized Oauth Apps <https://github.com/settings/applications>`_ and `GitHub:
Developer applications <https://github.com/settings/developers>`_ after
creation.

You need to add the redirect url, it will look something like
``https://YOURDOMAIN/accounts/github/login/callback/``.

GitHub does *not* support having multiple redirect urls on file simultaneously.

Example: Logging in with the bundled Feide OIDC (aka. dataporten) provider
--------------------------------------------------------------------------

Your organization needs to be paying for `Feide <https://www.feide.no/>`_.

The app for this does not need any additional tables so the below configuration
is all you need.

.. code-block:: toml

   [social.providers.dataporten]
   module-path = "allauth.socialaccount.providers.dataporten"
   client_id = "your.service.id"
   secret =  "your.service.secret"

You get the client id and secret from `Feide Kundeportal
<https://kunde.feide.no>`_, and you need to add the redirect url there. The
redirect url will look something like
``https://YOURDOMAIN/accounts/dataporten/login/callback/``.

.. tip::
   If you attempt to log in without the url set you will get an error-page that
   shows exactly what url you need to use.

Dataporten supports having multiple redirect urls on file simultaneously.

Using generic OIDC
==================

This may take *a lot more* configuration so check if there is a bundled
provider first.

Overview of settings:

.. code-block:: toml

   [oidc]
   # module-path = "your.oidc.provider.module"  # default
   #
   # Optional PKCE defaults to False, but may be required by your provider
   # Can be set globally, or per app (settings).
   # "OAUTH_PKCE_ENABLED": False,
   # oauth_pkce_enabled = false

   [oidc.idps.some-unique-id]  # this id must be urlsafe
   name = "Some Login System",  # Shown in the frontend
   client_id = "your.service.id", # Get from idp
   secret = "your.service.secret", # Get from idp
   server_url = "https://my.server.example.com"

   # [oidc.idps.some-unique-id.settings]  # optional settings
   # Optional PKCE defaults False, but may be required by
   # your provider
   # oauth_pkce_enabled = false
   #
   # When enabled, an additional call to the userinfo
   # endpoint takes place. The data returned is stored in
   # `SocialAccount.extra_data`. When disabled, the (decoded) ID
   # token payload is used instead.
   # fetch_userinfo = true
   #
   # Optional token endpoint authentication method.
   # May be one of "client_secret_basic", "client_secret_post"
   # If omitted, a method from the the server's
   # token auth methods list is used
   # token_auth_method = client_secret_basic
   #
   # scope = [],
   #
   # The field to be used as the account ID. Might depend on scope
   # uid_field = "sub"

You need to come up with a unique provider id. Note that it will be used
verbatim in the redirect url and that it must not conflict with any other
``provider_id`` or ``provider`` in use.

See `django-allauth: OpenID Connect
<https://docs.allauth.org/en/latest/socialaccount/providers/openid_connect.html>`_
for more details.

You can override the module used for OIDC by setting module-path explicitly:

.. code-block:: toml

   [oidc]
   module-path = "your.oidc.provider.module"

The ``server_url`` is just the first part of an url that ends with
``.well-known/openid-configuration`` used for OpenID Connect discovery.

.. note::
   Providers that come both bundled and have an OIDC endpoint are not
   equivalent, the former might have provider specific code.


Example: Logging in with Feide OIDC (dataporten) without using a provider app
-----------------------------------------------------------------------------

Using Feide OIDC (aka. dataporten) as an example

.. code-block:: toml

   [oidc.idps.dataporten-oidc]
   name = "Feide OIDC",  # Shown in the frontend
   client_id = "your.service.id",  # Get from your Feide admin
   secret = "your.service.secret",  # Get from your Feide admin
   server_url = "https://auth.dataporten.no/"

   # optional settings but needed for Feide OIDC
   [oidc.idps.dataporten-oidc.settings]
   uid_field = "https://n.feide.no/claims/eduPersonPrincipalName"
   scope = ["userid-feide"]

Just like when using a provider app you get the client id and secret from
`Feide Kundeportal <https://kunde.feide.no>`_, and you need to add the redirect
url there. The redirect url will look something like
``https://YOURDOMAIN/accounts/oidc/dataporten-oidc/login/callback/``.

.. tip::
   If you attempt to log in without the url set you will get an error-page that
   shows exactly what url you need to use.

.. note::
   If you choose "Client type": "Public" you must set ``oauth_pkce_enabled`` to
   True.

Dataporten supports having multiple redirect urls on file simultaneously.
