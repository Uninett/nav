===========
The NAV API
===========

Disclaimer
----------

**The API in NAV 4.0 is a proof-of-concept.** That basically means that it is
not really ready to use, lacks a lot of functionality and is subject to change.

About
-----

The NAV API gives access to NAV's data without needing to connect to the
database. You need a token and some way of sending an https request and you're
good to go.


Tokens
------

Authentication and authorization is done by tokens. Currently the API is very
simple - either you have access (a token) or you do not. Depending on the needs
that occur this may or may not change. The API is currently read-only.


How to get a token
------------------

You need to log in to the NAV installation you want data from as an
administrator. Then go to ``/api/token``. The string you see then is your token.


How to use the token
--------------------

The token needs to be included in all your requests. To test that your token is
working, use curl::

  curl -H 'Authorization: Token <token>' https://<host>/api/netboxes/

As you see, we use the ``Authorization`` header field to include the token. When
doing your requests, make sure to add the header field to all requests. 

**NB: These requests should never, ever be done unencrypted.** Do not use this
on NAV installations that do not have SSL enabled, you are potentially giving
everyone access to the data.


Data format
-----------

The NAV API currently only outputs JSON formatted data. Other output formats may
be included in the future.


Current available endpoints
---------------------------

The following urls will provide you with data:

- ``/api/netboxes/``
- ``/api/netboxes/<id>``
- ``/api/rooms/``
- ``/api/rooms/<id>``
- ``/api/prefixes/``
- ``/api/prefixes/<id>``


Planned additions
-----------------

The API as it is lacks a lot of functionality. This is a list of some of the
things that are planned:

- Add an api root
- Add filtering and search
- Saner urls (i.e. netboxes/ -> netbox/)
- Make api browsable from NAV
- Make more data availble
- API versioning
