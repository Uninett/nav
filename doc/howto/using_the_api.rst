===========
The NAV API
===========

About
=====

The NAV API gives access to NAV's data without needing to connect to the
database. You need a token and some way of sending an https request and you're
good to go.


Tokens
======

Authentication and authorization is done by tokens. A token gives you access to
zero or more endpoints and read or read and write permissions. *Not all endpoints
support write operations*.


How to get a token
------------------

Tokens are administrated from the ``User and API Administration`` page in NAV.

.. _classic-token:
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

.. _jwt-token:
JSON Web Tokens
------------------
JSON Web Tokens (JWTs) must be :ref:`configured <jwt-configuration>` before they can be used.

Once configured, you can use tokens issued by your configured issuers in almost the same way
as :ref:`classic tokens <classic-token>`::

  curl -H 'Authorization: Bearer <token>' https://<host>/api/netboxes/

Note how JWTs require the prefix ``Bearer`` and not ``Token``.

JWTs must include valid ``exp``, ``nbf``, ``iss`` and ``aud`` claims in order to be valid.
``iss`` and ``aud`` must match the :doc:`configuration <../reference/jwt>`, while ``exp`` must
be in the future and ``nbf`` must be in the past.

The ``endpoints`` and ``write`` claims are optional claims that are used to determine what
resources the token has access to.
The ``endpoints`` claim should contain a list of endpoints that the token has access to.
If ``endpoints`` is an empty list or omitted, the token will not have access to any endpoints.
The ``write`` claim should be a boolean indicating whether the token has write access to the endpoints.
If ``write`` is ``false`` or omitted, the token will only have read access to the endpoints listed in ``endpoints``.


Locally issued JSON Web Tokens
------------------------------
Local JSON Web Tokens (JWTs) must be :ref:`configured <local-jwt-configuration>` before they can be used.

NAV supports generating JWT tokens for local use, as opposed to tokens generated externally.
You can generate refresh tokens via the frontend which can be used to obtain access tokens
that can be used as described :ref:`above <jwt-token>`.

In order to create access tokens you must use the refresh token endpoint, which is available at ``/api/jwt/refresh/``.
The endpoint takes a JSON object with a single key, ``refresh_token``, which should contain the
token you wish to use::

  curl -X POST -H "Content-type: application/json" http://localhost:80/api/jwt/refresh/ -d '{"refresh_token": "<refresh_token>"}'

The response will contain an access token and a new refresh token::

  {"refresh_token": "<new_refresh_token>", "access_token": "<new_access_token>"}

Refresh tokens can only be used once, so the next time you need a new access token,
you should use the new refresh token provided in the response.


Browsing the API
================

The NAV API currently only outputs JSON formatted data. Other output formats may
be included in the future.

The API is semi-browsable with a browser. As it uses the token to authenticate
and authorize, you need to find a way to include that in your browser
requests. If you use Chrome this can be used with the extension
``ModHeader``. As the output is JSON and not HTML, we also recommend the
extension ``JSON Formatter`` or similar.


Available endpoints
-------------------

The available endpoints is listed if you go to the root of the api -
``/api/``. These endpoints are:

- "alert": "http://<host>/api/alert/"
- "arp": "http://<host>/api/arp/"
- "cam": "http://<host>/api/cam/"
- "room": "http://<host>/api/room/"
- "netbox": "http://<host>/api/netbox/"
- "interface": "http://<host>/api/interface/"
- "prefix": "http://<host>/api/prefix/"
- "prefix_usage": "http://<host>/api/prefix/usage"
- "prefix_routed": "http://<host>/api/prefix/routed"

These endpoints will give list output limited by page size and any optional
search or filter parameters (more about that below).

The :doc:`endpoint parameters <api_parameters>` are separately documented.


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

Searching
^^^^^^^^^

Searching is done by using the parameter ``search``::

  /api/netbox/?search=something

The fields used in the search are determined by the NAV developers. An effort to
determine sane search fields has been done, but if you notice strange search
results please notify us so we can correct it.

Filtering
^^^^^^^^^

A filter is more specific than a search in that you explicitly define what field
you are using and exactly the value it should have::

  /api/netbox/?category=GSW

At the moment there is no way of specifying wildcards in the filter.


Using POST, PUT, PATCH and DELETE
---------------------------------

To use these request methods you need a write-enabled token. Go to ``User and API
Administration`` to set token attributes.

CRUD-methods are enabled for a limited number of endpoints. These endpoints can
be found by querying the endpoint with the ``OPTIONS`` header and see if POST is
in the ``Allow`` header. You will also see what fields are required.

POST
^^^^

Used to create new entries. Operates on the list of entries::

  curl -i -H 'Content-Type: application/json' -H 'Authorization: Token <token>' -XPOST 'http://localhost/api/1/netbox/' -d '{
        "ip": "158.38.xxx.xxx",
        "roomid": "teknobyen",
        "organizationid": "uninett",
        "categoryid": "SW",
        "snmp_version": 2}'


PUT
^^^

Used on single entries to create or update. PUT needs all required fields for
each request::

  curl -i -H 'Content-Type: application/json' -H 'Authorization: Token <token>' -XPUT 'http://localhost/api/1/room/<id>/' -d '{"id": "<id>", "location": "trondheim"}'

PATCH
^^^^^

Used to update single entries::

  curl -i -H 'Content-Type: application/json' -H 'Authorization: Token <token>' -XPATCH 'http://localhost/api/1/netbox/<id>/' -d '{"roomid": "teknobyen"}'

DELETE
^^^^^^

Used to delete single entries::

  curl -i -H 'Authorization: Token <token>' -XDELETE 'http://localhost/api/1/netbox/<id>/'



A specific scenario
-------------------

We want to know the interface a computer is connected to right now. We have the
ip-address of the computer.

First find the correct arp object::

  /api/arp/?ip=10.1.1.1&active=true

  {
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 996604,
        "netbox": 35,
        "prefix": null,
        "sysname": "sysname.no",
        "ip": "10.1.1.1",
        "mac": "00:00:00:00:00:00",
        "start_time": "2014-04-24T15:00:43.712",
        "end_time": "9999-12-31T23:59:59.999"
      }
    ]
  }

The active parameter specifies that we only want results that are active
now. The result from this query gives us the mac address of the computer. We
need that to find the interface it is connected to::

  /api/cam/?mac=00:00:00:00:00:00&active=true

  {
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 875800,
        "netbox": 11,
        "sysname": "generic_switch.no",
        "ifindex": 229,
        "module": "",
        "port": "A00",
        "start_time": "2014-05-13T13:09:40.296",
        "end_time": "9999-12-31T23:59:59.999",
        "miss_count": 0,
        "mac": "00:00:00:00:00:00"
      }
    ]
  }

This gives us access to the IP Device (netbox) id and the ifindex of the interface. We
use that to find the correct interface::

  /api/interface/?netbox=11&ifindex=229

  {
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 329955,
        "netbox": 11,
        "module": 5996,
        "ifindex": 229,
        "ifname": "A00",
        "ifdescr": "A00",
        "iftype": 6,
        "speed": 1000,
        "ifphysaddress": "01:23:45:67:89:01",
        "ifadminstatus": 1,
        "ifoperstatus": 2,
        "iflastchange": null,
        "ifconnectorpresent": true,
        "ifpromiscuousmode": false,
        "ifalias": "Some description",
        "baseport": 55,
        "media": null,
        "vlan": 20,
        "trunk": false,
        "duplex": "f",
        "to_netbox": 85,
        "to_interface": null,
        "gone_since": null
      }
    ]
  }

We now have the correct interface that the computer is connected to right
now.
