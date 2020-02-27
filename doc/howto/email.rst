-------------------
Robustifying e-mail
-------------------

Most e-mail sent is spam, and making sure e-mail reaches its intended
recipients keeps getting harder.

Single server installations
---------------------------

When running only a single NAV-instance, sending ``cron`` e-mail and alerts and perhaps receiving on ``mailin@HOSTNAME``, the instance needs to be treated like any other e-mail sending server. Set up SPF and preferrably also DKIM.

Multi server installations
--------------------------

If there are multiple instances of NAV working in tandem we recommend sending the e-mail out via a smarthost and standardising on a single domain, for instance ``nav.YOURDOMAIN`` and setting up SPF/DKIM for that domain.

For ``cron``, change the localpart (the bit before the ``@``) to contain enough of the hostname so that you can see what instance sent the e-mail, for instance:
``root=nav-3rdstreet@nav.example.com``. This is best done by running an e-mail server on the instance to do the rweriting, before sending the e-mail on to the
smarthost.

For alerts, this should not be necessary as long as the template mentions which host sent the alert. Just send from a single e-mail address.

For ``mailin``, if you have an e-mail server listening on ``nav.YOURDOMAIN`` you can set up an e-mail router with aliases back to the ``mailin``-address on the actual instance if the address you register with the senders are unique per instance (e.g. in an ``aliases``-file)::

   mailin=nav-3rdstreet:    mailin@nav-3rdstreet.nav.example.com

If you do not switch to a single domain for all the instances you will have to set up SPF/DKIM per hostname.
