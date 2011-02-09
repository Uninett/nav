========
 MailIn
========

MailIn provides a simple engine for transforming e-mail alerts from 3rd party
software into NAV events.  These events can then be processed by NAV's event-
and alert systems.

See also `the original blueprint specification for MailIn
<http://metanav.uninett.no/devel:blueprints:mailin>`_.


Configuring MailIn
------------------

These examples all assume your NAV installation prefix is the default
``/usr/local/nav``.

Redirecting mail to the mailin program
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pick an e-mail address on your NAV server to send 3rd party alerts to, for
example `mailin@nav.example.org`.  Mail received at this address should be
piped through the ``mailin.py`` program.  This can usually be accomplished by
adding an e-mail alias to ``/etc/aliases``, like this::

  cat >> /etc/aliases <<EOF
  mailin: "| PYTHONPATH=/usr/local/nav/lib/python /usr/local/nav/bin/mailin.py"
  EOF
  newaliases

Selecting plugins
~~~~~~~~~~~~~~~~~

Add the plugins you want to use to the ``plugins`` variable in
your ``mailinf.conf`` file. For example::

  plugins =
    nav.mailin.plugins.whatsup
    nav.mailin.plugins.kake

The plugins will be tried in the order they are listed in the config file, so
if the ``whatsup`` plugin accepts the message here, ``kake`` will never be
called.

Alert message templates
~~~~~~~~~~~~~~~~~~~~~~~

Each plugin will define its own set of event and alert types for its domain.
You will want to add alert message templates for these alerts in
``alertmsg.conf``.

Here's an example for the ``whatsup`` plugin, which defines the ``whatsup``
event type::

  whatsup {
    default {
      email {
	no {
	  Subject: $subject
	  $body
	}
	en {
	  Subject: $subject
	  $body
	}
      }
      sms {
	en: $subject
	no: $subject
      }
    }
  }

This example adds Norwegian and English templates for both `email` and `sms`
alert channels.
