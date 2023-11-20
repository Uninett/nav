======
 smsd
======

The SMS daemon takes care of sending alerts queued for SMS dispatch.

The daemon will regularly check the `smsq` database table via a generalized
queue module.  Any new messages are dispatched via one or more dispatchers
with a generic interface. Support for multiple dispatchers are handled by a
dispatcher handler layer.

Usage
=====

For more help on usage, run ``smsd --help`` and see the ``smsd.conf`` config
file.


Message queues
==============

Message queues are generic producers of SMS messages in `smsd`.  At the
moment, only the :py:class:`nav.smsd.navdbqueue.NAVDBQueue` implementation is
available, which will produce SMS messages from the ``smsq`` table in the NAV
database.

Other message queue implementations can be written using the same interface as
implemented by :py:class:`nav.smsd.navdbqueue.NAVDBQueue`.

Dispatchers
===========

smsd delegates the actual dispatch of messages to dispatcher plugins.  Plugins
can be configured in prioritized order in ``smsd.conf``.

Available dispatchers
---------------------

GammuDispatcher
~~~~~~~~~~~~~~~

:description:

	The Gammu dispatcher uses `Gammu` to send SMS messages via a cell phone
	connected to the server with a serial cable, USB cable, IR or
	Bluetooth. See http://www.gammu.org/ for more information.

:depends:

	Depends on the ``gammu`` Python binding.  As a prerequisite, the
	`navcron` user must have write privileges to the device where the
	Gammu-configured mobile phone is connected.

:pros:

	Works as long as the mobile carrier is up and running, independent of
	your own network.

:cons:

	You will need a dedicated mobile phone or other GSM device.

HttpGetDispatcher
~~~~~~~~~~~~~~~~~

:description:

	Originally contributed by USIT, University of Oslo for use with their
	HTTP-to-SMS gateway. Generalized to be useful for similar gateways
	without UiO's exact URL syntax. Supports both HTTP and HTTPS.

:depends:

	Depends on ``urllib`` and ``urllib2``, which both are parts of core
	Python.

:pros:

	Does not need a dedicated mobile phone.

:cons:

	Depends on a working network connection between you and your
	HTTP-to-SMS gateway. Does not support POST or HTTP Basic Auth.

BoostDispatcher
~~~~~~~~~~~~~~~

:description:

	This dispatcher sends SMS via Boost Communications' WebService (`SOAP`).
	See http://www.boostcom.no/ for more information.

	.. NOTE:: The dispatcher is provided as a proof-of-concept only; it
	          seems it no longer conforms to Boost's newest APIs.

:depends:

	Depends on ``SOAPpy`` (``python-soappy`` in Debian).
	Requires a username and password to send SMS using the SOAP interface.
	Contact http://www.boostcom.no/ to setup a contract for their External
	Sender product.

:pros:

	Does not need a dedicated mobile phone.

:cons:

	Depends on a working network connection between you and Boost
	Communcations.

UninettMailDispatcher
~~~~~~~~~~~~~~~~~~~~~

:description:

	This dispatcher sends SMS via Sikt's (previously Uninett) `email-to-SMS` gateway.
	Sikt's gateway only works internally, but this plugin can serve as
	a proof-of-concept for someone implementing a similar service.  The
	e-mail adress is configurable in ``smsd.conf``.

:depends:

	Only depends on ``smtplib``, which is a part of core Python (of
	course, a working SMTP server is required also).

:pros:

	If you have an email-to-SMS gateway that accepts e-mails where the
	subjects is a phone number and the body is an SMS text message, there
	is no extra setup cost to get the daemon sending SMS messages.

:cons:

	Unless you have a similar email-to-SMS gatway, this only works for
	Sikt.

Extending
=========

Write your own dispatcher by extending the
:py:class:`nav.smsd.dispatcher.Dispatcher` class.  You can also implement your
own message queue by implementing the same interface as the
:py:class:`nav.smsd.navdbqueue.NAVDBQueue` class.

nav.smsd.dispatcher
-------------------
.. automodule:: nav.smsd.dispatcher
   :members:
   :undoc-members:

nav.smsd.navdbqueue
-------------------
.. automodule:: nav.smsd.navdbqueue
   :members:
   :undoc-members:
