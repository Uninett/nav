===========
The NAV API
===========

Disclaimer
----------

**The API in NAV 4.1 is in it's infancy.** Expect some rough edges.

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


Browsing the API
----------------

The API is semi-browsable with a browser. As it uses the token to authenticate
and authorize, you need to find a way to include that in your browser
requests. If you use Chrome this can be used with the extension
``ModHeader``. As the output is JSON and not HTML, we also recommend the
extension ``JSON Formatter`` or similar.


Available endpoints
-------------------

The available endpoints is listed if you go to the root of the api - ``/api/``.


Paging
------

The API supports paging of results. The current default maximum number of
results from a query is 100. If the query returns more than that, it will
provide a link to the next page of results.

You can specify the number of results on a page by setting the ``page_size``
parameter in your request.


Searching and filtering
-----------------------

The API supports searching and filtering of data. A search is different from
a filter in that a filter is more specific.
