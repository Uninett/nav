===========================
MUlti-factor authentication
===========================

Multi-factor authentication (aka. 2-factor athentication or "2FA") needs to be
enabled site-wide before it is available. This includes support for passkeys
aka. webauthn.

The configuration is stored in the ``[multi-factor-authentication]`` section of
:file:`webfront.conf`.

The default settings are::

    [multi-factor-authentication]
    enabled = no
    support-recovery-codes = yes
    support-passkeys = no
    support-passkey-signups = no
    allow-insecure-origin = no

Changing ``enabled`` to ``yes`` will turn on TOTP support, including 10
recovery keys per account. Turn off recovery keys support by toggling
``support-recovery-codes`` to ``no``.

The three other settings controls passkeys. ``allow-insecure-origin`` should
stay ``no`` in production, it is meant prinarily for development.

There is currently no way to force the activation of second factor support on
first login, or activate a second factor on behalf of someone else.

Locally controlled 2FA is incompatible with using REMOTE_USER to log in, pick one.
