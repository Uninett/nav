========
 MailIn
========

MailIn provides a simple engine for transforming e-mail alerts from 3rd party
software into NAV events.  These events can then be processed by NAV's event-
and alert systems.

See also `the original blueprint specification for MailIn
<https://nav.uninett.no/wiki/devel:blueprints:mailin>`_.


Configuring MailIn
------------------

These examples all assume your NAV installation prefix is the default
``/usr/local/nav``.

Redirecting mail to the MailIn program
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The mail transfer agent on your NAV server must be configured to accept SMTP
connections from outside the server, or no messages will come through.

Pick an e-mail address on your NAV server to send 3rd party alerts to, for
example `mailin@nav.example.org`.  Mail received at this address should be
piped through the ``mailin`` program.  This can usually be accomplished by
adding an e-mail alias to :file:`/etc/aliases`, like this::

  cat >> /etc/aliases <<EOF
  mailin: "| /usr/local/nav/bin/mailin"
  EOF
  newaliases

Also, for ``mailin.py`` to work properly, it needs write access to its log
file. Your mail delivery agent will likely run the program under a user ID
that has no write access to the file. Consult your MDA documentation; a
typical choice for Postfix on a Debian system is to run external commands as
the user ``nobody``. Make sure to change ownership of the log file::

  chown nobody /usr/local/nav/var/log/mailin.log


Selecting plugins
~~~~~~~~~~~~~~~~~

Add the plugins you want to use to the ``plugins`` variable in
your :file:`mailin.conf` file. For example::

  plugins =
    nav.mailin.plugins.whatsup
    nav.mailin.plugins.kake

The plugins will be tried in the order they are listed in the config file, so
if the ``whatsup`` plugin accepts the message here, ``kake`` will never be
called.

Alert message templates
~~~~~~~~~~~~~~~~~~~~~~~

Each plugin will define its own set of event and alert types for its
domain. The example plugins come with their own alert message templates in the
:file:`/usr/local/nav/etc/alertmsg/` directory, but if you write your own
plugins with your own event and alert types, you will need to write your own
alert message templates in this directory as well.

Here's an example for the ``whatsup`` plugin, which defines the ``whatsup``
event type. Each event it generates contains the ``subject`` and ``body``
variables, which can be referenced in the alert message templates:

1. For email alerts there's :file:`alertmsg/whatsup/default-email.txt`::

    Subject: {{ subject }}

    {{ body }}

   For email alerts, the first line of the template should always start with
   ``Subject:``, which causes the rest of that line to be used as the subject
   header of the sent email.

2. For SMS alerts there's :file:`alertmsg/whatsup/default-sms.txt`::

    {{ subject }}

   The subject variable is usually short and appropriate for a quick SMS
   alert.
