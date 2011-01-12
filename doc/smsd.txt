What is smsd?
=============
The NAV SMS daemon, which takes care of sending alerts queued for SMS dispatch.

What does it do?
================
The daemon is quite standalone, and only gets some paths and config from NAV.
In short it checks the smsq database table regularly via a generalized queue
module, formats the messages into one SMS and dispatches it via one or more
dispatchers with a general interface. Support for multiple dispatchers are
handled by a dispatcher handler layer.

Usage
=====
For more help on usage, run ``smsd.py --help'' and see the smsd.conf config
file.

Development
===========
For more help on developing new queues or dispatchers, see the pydoc of the
various modules in nav.smsd and the well documented source code.

What message queues are available?
==================================
At this point only the NAVDBQueue is available, as this is all that is needed
to use the SMS daemon in a NAV setup. The queue is although separated so it
should not require a large rewrite to use the SMS daemon in a totally different
setup than NAV.

What dispatchers are available?
===============================
GammuDispatcher
---------------
Description:
	The Gammu dispatcher uses Gammu to send SMS messages via a cell phone
	connected to the server with a serial cable, USB cable, IR or
	Bluetooth. See http://www.gammu.org/ for more information.
Depends:
	Depends on python-gammu (name of the Debian package).
	As a prerequisite, Gammu has to be configured to work as the navcron
	user.
Pros:
	Works as long as the mobile carrier is up and running, independent of
	your own network.
Cons:
	You will need a dedicated mobile phone.

HttpGetDispatcher
-----------------
Description:
	Originally contributed by USIT, UiO for use with their HTTP-to-SMS
	gateway. Generalized to be useful for similar gateways without UiO's
	exact URL syntax. Supports both HTTP and HTTPS.
Depends:
	Depends on urllib and urllib2, which both are parts of core Python.
Pros:
	Does not need a dedicated mobile phone.
Cons:
	Depends on a working network connection between you and your
	HTTP-to-SMS gateway. Does not support POST or HTTP Basic Auth.

BoostDispatcher
---------------
Description:
	This dispatcher sends SMS via Boost Communications' WebService (SOAP).
	See http://www.boostcom.no/ for more information.

	The dispatcher has known problems (see SF#1661395), but as we do not
	have access to a Boost account for testing, this dispatcher should be
	regarded as a proof of concept.
Depends:
	Depends on SOAPpy (python-soappy in Debian).
	Requires a username and password to send SMS using the SOAP interface.
	Contact http://www.boostcom.no/ to setup a contract for their External
	Sender product.
Pros:
	Does not need a dedicated mobile phone.
Cons:
	Depends on a working network connection between you and Boost
	Communcations.

UninettMailDispatcher
---------------------
Description:
	This dispatcher sends SMS via UNINETT's mail-to-SMS gateway. The mail
	must be sent from a uninett.no host, so this is of little use for
	others, but is useful as a proof of concept.
Depends:
	Only depends on smtplib which is a part of core Python.
	And, of course, on a working SMTP server.
Pros:
	No extra setup cost to get the daemon sending SMS messages.
Cons:
	Only works for UNINETT or if you have implemented a similar mail-to-SMS
	gateway. If you have your own mail-to-SMS gateway, take contact, and we
	will find a way to generalize this into a MailDispatcher.


-- Stein Magnus Jodal <stein.magnus.jodal@uninett.no>, 2006-07-03
   Updated 2007-02-19.
