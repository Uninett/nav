==============================================================
Authenticating with OIDC/OAuth2 by using a local settings file
==============================================================

It is possible to use a local settings-file to unlock every option available in
`django-allauth <https://docs.allauth.org/en/latest/>`_'s arsenal but we will
only show how to support bundled and OIDC providers here. Have a look at
:doc:`../hacking/extending-nav-locally` for where to put the local settings
file.

The file MUST start with:

.. code-block:: python
   :caption: ${configdir}/python/local_settings.py

   LOCAL_SETTINGS = True
   from nav.django.settings import *

A complete list of relevant allauth settings are at `django-allauth's third
party account configuration
<https://docs.allauth.org/en/latest/socialaccount/configuration.html>`_
documentation.

The most important setting is ``SOCIALACCOUNT_PROVIDERS``. It is is generally of the form:

.. code-block:: python

   SOCIALACCOUNT_PROVIDERS = {
       'provider-specific-id': {
           "APPS": [
                {
                     "client_id": "123",  # ask provider for this
                     "secret": "hjkkj",  # ask provider for this
                     "key": "ghffgh",  # ask provider for this, often optional
                     "settings": {
                        # depends
                     },
                },
           ],
           # SCOPE is optional
           'SCOPE': [
                'provider',
                'specific',
                'strings'
           ],
       }
   }

.. warning::
   Groups and roles fetched via OIDC/OAuth2 is currently not supported in
   NAV, as there is as of yet no standardized way to do so.

.. note::
   NAV does not currently support sign up on first login, aka auto signup.
   Create a local user first, then let that logged in user activate a login
   provider via "HOME /ACCOUNT / ACCOUNT CONNECTIONS".

Using a provider bundled with django-allauth
============================================

In addition to setting ``SOCIALACCOUNT_PROVIDERS`` you'll need to add an app,
per provider. An app might depend on a database table that is not installed in
NAV so you need to check and if necessary add the tables yourself.

Find a complete list of provider settings that come bundled with
allauth at `django-allauth's provider list
<https://docs.allauth.org/en/latest/socialaccount/providers/index.html>`_

Example: Logging in with the bundled GitHub provider
----------------------------------------------------

Anyone can get an account at GitHub so we're using that as the most basic example.

See `Authorizing OAuth apps
<https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps>`_
for details.

The app for this does not need any additional tables so the below configuration
is all you need.

.. code-block:: python

   INSTALLED_APPS += tuple(["allauth.socialaccount.providers.github"])

   SOCIALACCOUNT_PROVIDERS = {
       "github": {
           "APP": {
               "client_id": "your.service.id",
               "secret": "your.service.secret",
           },
       }
   }

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

.. code-block:: python

   INSTALLED_APPS += tuple(["allauth.socialaccount.providers.dataporten"])

   SOCIALACCOUNT_PROVIDERS = {
       "dataporten": {
           "APP": {
               "client_id": "your.service.id",
               "secret": "your.service.secret",
           },
       }
   }

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

.. code-block:: python

   SOCIALACCOUNT_PROVIDERS = {
       "openid_connect": {
           # Optional PKCE defaults to False, but may be required by your provider
           # Can be set globally, or per app (settings).
           # "OAUTH_PKCE_ENABLED": True,
           "APPS": [
               {
                   "provider_id": "some_urlsafe_unique_string",
                   "name": "Some Login System",  # Shown in the frontend
                   "client_id": "your.service.id",  # Get from your Feide admin
                   "secret": "your.service.secret",  # Get from your Feide admin
                   "settings": {
                       # Optional PKCE defaults False, but may be required by
                       # your provider
                       # "oauth_pkce_enabled": False,
                       "server_url": "https://my.server.example.com",
                       # When enabled, an additional call to the userinfo
                       # endpoint takes place. The data returned is stored in
                       # `SocialAccount.extra_data`. When disabled, the (decoded) ID
                       # token payload is used instead.
                       # "fetch_userinfo": True,
                       # Optional token endpoint authentication method.
                       # May be one of "client_secret_basic", "client_secret_post"
                       # If omitted, a method from the the server's
                       # token auth methods list is used
                       # "token_auth_method": "client_secret_basic",
                       # "scope": [],
                       # The field to be used as the account ID. Might depend on scope
                       "uid_field": "sub",
                   },
               },
           ]
       }
   }

Note that the ``provider_id`` will be used verbatim in the redirect url and
that it must not conflict with any other ``provider_id`` or ``provider`` in
use.

See `django-allauth: OpenID Connect
<https://docs.allauth.org/en/latest/socialaccount/providers/openid_connect.html>`_
for more details.

.. note::
   Providers that come both bundled and have an OIDC endpoint are not
   equivalent, the former might have provider specific code.


Example: Logging in with Feide OIDC (dataporten) without using a provider app
-----------------------------------------------------------------------------

Using Feide OIDC (aka. dataporten) as an example

.. code-block:: python

   INSTALLED_APPS += ("allauth.socialaccount.providers.openid_connect",)

   SOCIALACCOUNT_PROVIDERS = {
       "openid_connect": {
           "APPS": [
               {
                   "provider_id": "dataporten-oidc",
                   "name": "Feide OIDC",  # Shown in the frontend
                   "client_id": "your.service.id",  # Get from your Feide admin
                   "secret": "your.service.secret",  # Get from your Feide admin
                   "settings": {
                       # "oauth_pkce_enabled": True,
                       "server_url": "https://auth.dataporten.no/",
                       "uid_field": "https://n.feide.no/claims/eduPersonPrincipalName",
                       "scope":[
                           "userid-feide",
                       ],
                   },
               },
           ]
       }
   }

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
