===========================
Multi-factor authentication
===========================

Multi-factor authentication (aka. 2-factor authentication or "2FA") needs to be
enabled site-wide before it is available. If disabled, the ``My account``-page
will have a tab mentioning that it is disabled. After enabling, that tab will
change to allow the logged in user to set up 2FA for themselves.

The configuration is stored in the ``[multi-factor-authentication]`` section of
:file:`webfront/authentication.toml`.

The default settings are::

    [multi-factor-authentication]
    enabled = false
    support-recovery-codes = true

Changing ``enabled`` to ``true`` will turn on TOTP support, including 10
recovery keys per account. Turn off recovery keys support by toggling
``support-recovery-codes`` to ``false``.

There is no way to force the activation of second factor support on first
login, or activate a second factor on behalf of someone else via sudo, as the
beneficiary's own password is needed.

Locally controlled 2FA is incompatible with using REMOTE_USER to log in, pick one.
