========
 Geomap
========

The Geomap tool is a web app that renders your network topology on a
geographical map, provided that you have seeded your room data with
geographical coordinates.

Geomap is powered by OpenLayers_, and the underlying map data is
provided by OpenStreetMap_.

-----------------------
Technical documentation
-----------------------

The server-side part is written in Python and the client-side in
JavaScript.  These are described separately below.

The server-side code is in the :py:mod:`nav.web.geomap` module,
while the client-side code is in the directory ``media/js/geomap``.


URLs and parameters
===================


URLs
----

There are two types of resources in Geomap:

1. The web page showing the map ( ``/geomap/[variant]/`` )
2. Geographical network data in GeoJSON or KML format
   ( ``/geomap/[variant]/data?[parameters]`` )

Where ``[variant]`` represents a variant name defined in the configuration
file.  The URL ``/geomap`` redirects to ``/geomap/[v]/``, where ``[v]`` is the
first variant the user has access to.


Query string parameters
-----------------------

The map web page accepts the following parameters in the query string
(these are used by the JavaScript code only; the server side code
ignores them):

``bbox``
  Bounding box of area to display.  The format of this field follows the
  definition of the "box" parameter in the `OpenSearch Geo extension`_
  (a dump of the original wiki site can also be found on `Github`_).

``lat`` and ``lon``
  Position for center of map

``zoom``
  Zoom level for map (0-18)

``layers``
  Description of which layers to show.  For each layer in the map, one of the
  characters 'B' (base layer, displayed), '0' (base layer, not displayed), 'T'
  (non-base layer, displayed), 'F' (non-base layer, not displayed).

``time``
  Selected time interval for load data.  Interval size (index, 1-5), dash,
  start time (``YYYYMMDDhhmm`).  The interval sizes are: 1: month; 2: week; 3:
  day; 4: hour; 5: 10 minutes.  (See ``media/js/geomap/TimeInterval.js``)

The arguments (``lat``, ``lon``, ``zoom``, ``layers``, ``time``) are intended
to be used together.  They specify (more or less) the complete state of the
user interface, and are used by the «Link to this configuration» link, which
sets up these arguments to reflect the current state.

The ``bbox`` argument is not intended to be used together with the other
arguments (the arguments ``lat``, ``lon`` and ``zoom``, if present, override
the ``bbox`` argument).  The ``bbox`` argument is meant as a way for other
applications to be able to create links to Geomap for showing a certain area.


The data resource accepts the following parameters in the query
string:

``format``
  Data format for result, either ``geojson`` or ``kml``.

``bbox``
  Bounding box of map area.

``viewport{Width,Height}``
  Size (in pixels) of map as shown in user agent.

``limit``
  How close (in pixels) two nodes may be before they are collapsed to one.

``time{Start,End}``
  Time interval for load data, in the form expected by rrdfetch_ for its
  ``--start`` and ``--end`` options.


Server
======


Overview
--------

Almost all the server-side code is involved with generating the data
resource.  The web page showing the map requires almost no server-side
processing.

Data flows in pipeline style through the modules :py:mod:`db`,
:py:mod:`graph`, :py:mod:`features`, :py:mod:`output_formats`; each of which
has as its main purpose the transformation of data from one form to another.
Except for the data representations which constitute the interfaces from one
part of the pipeline to the next, these modules are mutually independent.  The
data flow is controlled by the function :py:func:`views.get_formatted_data`.

The :py:mod:`conf` module reads and parses Geomap's configuration file.  The
:py:mod:`utils` module provides general utility functions/classes which are
used freely in the other modules.


Data pipeline
-------------

The :py:mod:`db` module collects data from the database and `RRD` files based
on the query string arguments.  The result is two dictionaries, representing
netboxes and connections, respectively.  Each netbox is represented as a
dictionary; each connection as two dictionaries (one for each end).

The :py:func:`graph.build_graph` function creates a graph structure from the
dictionaries the :py:mod:`db` module creates, while :py:func:`graph.simplify`
removes uninteresting things from such a graph.  The simplification consists
of:

1. removing objects which are outside the viewing area; and

2. reducing the level of detail by collapsing sets of objects which are close
   to each other to single objects.

The resulting simplified graph contains pointers to all the original
data in the form of a tree in each node (since nodes are collapsed in
two stages, see below) and a list in each edge.

For nodes, the collapsing is done in two steps: First, all the
netboxes in a single room are combined to one node.  Next, rooms that
are sufficiently close to each other are combined to "places".  After
the nodes are collapsed thus, any edges with the same two places as
their endpoints are combined to one edge.

The :py:mod:`features` module converts a graph to a set of "features",
i.e. nodes and lines with geographical coordinates.  Each feature has an
associated style (`color` and `width`/`radius`) and a specification of a popup
box for the feature.

The :py:mod:`output_formats` module converts a list of features to a string in
`GeoJSON` or `KML` format (for `KML` output, some information is lost).


Tricks to avoid reading RRD files: Cache, pseudo-laziness
---------------------------------------------------------

Load data is read from `RRD` files.  Each netbox/connection has its own file
(each connection actually has two), so we may end up reading very many files.
To avoid much file reading, we do two things:

1. Use a data structure inspired by lazy evaluation to avoid reading files
   which are not needed.
2. Cache values read from RRD files.

For `1`, we use the :py:class:`utils.lazy_dict` class.  An instance of
this class acts like a dictionary, but may contain values which are
not computed before they are looked up.  This way, the code may be
written almost as if all the files were read in the beginning (one
must be a little careful to avoid unintentionally causing all values
to be evaluated), while only those files which turn out to be needed
are actually read.

For `2`, we use Django's caching framework.  See the section labeled
"Cache" in ``db.py``.


Client-side
===========


Overview
--------

The client-side part of Geomap is written in JavaScript and uses the
OpenLayers library for all the difficult stuff.

.. image:: client-file-dependencies.svg
   :width: 100%

This diagram shows dependency relations between the JavaScript files and
libraries.  Rectangles represent JavaScript files, ellipses external
libraries.  When a file depends on another both directly and indirectly, the
direct relation is not drawn, to avoid cluttering the diagram with too many
arrows.  The complete diagram would be something close to the transitive
closure of the one drawn.

The file ``util.js`` is not shown in the diagram (all files implicitly depend
on it).  This file contains general utility functions which are used in other
files as if they were part of the standard library.

Most of the files provide somewhat more general functionality than what is
strictly needed in Geomap, and are intended to be mostly independent of each
other.  The file ``geomap.js`` instantiates all needed things from the other
files and connects them together.

The entry point for the client-side code is the function ``init``, defined in
``geomap.js``.  This function is called when the page is loaded, through the
``ONLOAD`` attribute on the ``BODY`` element.


Filename conventions
--------------------

Any file whose name starts with an uppercase character defines a data type
(`class`) of the same name (and defines few or no other names at the
top-level).  For some of the files which depend on OpenLayers_, the data type
defined is an extension of an OpenLayers class.  For other files, the data
type definition consists of a constructor function and a prototype object.

Any other file simply contains a collection of functions, and
introduces no new named data types.


External libraries
------------------

OpenLayers_
~~~~~~~~~~~

The OpenLayers_ library is included directly from the http://openlayers.org
site.  The URL we use always points to the newest version.

.. NOTE:: This may cause the NAV side of things to break if the OpenLayers API
   changes in a non-compatible way. On the other hand, keeping it at a fixed
   version has proved to be problematic because we include code from
   OpenStreetMap, and this code apparently depends on the newest version of
   OpenLayers (shortly after OpenLayers 2.8 was released, using the
   OpenStreetMap code with OpenLayers 2.7 did not work).

There are two sets of online code documentation pages for OpenLayers:
API documentation and documentation of everything.  The first contains
only the functions which are explicitly marked with "API" in the code.
One should generally stick to the API documentation, since other
functions are probably regarded as internal and likely to change.
However, there seems to be some "API" labels lacking here and there,
so sometimes it is useful to compare with the full documentation (or
the source code).

================================= ==========================================================
API documentation for OpenLayers  https://openlayers.org/en/latest/apidoc/
Full documentation for OpenLayers https://openlayers.org/en/latest/doc/
================================= ==========================================================


OpenStreetMap_
~~~~~~~~~~~~~~

We include a JavaScript file from OpenStreetMap_ which provides OpenLayers
classes for showing OpenStreetMap data.

The reference to the file was found here:
http://wiki.openstreetmap.org/wiki/OpenLayers_Simple_Example


Proj4js_
~~~~~~~~

We include the Proj4js_ library for coordinate transformations.  We do
not use this library directly, only through OpenLayers.  (OpenLayers
checks to see if Proj4js is available and uses it if it is).

The library is necessary to perform the conversions to/from UTM in
``coordinates.js``, which again is used by ``PositionControl.js``, which shows
the coordinates for a point the user clicked on the map.


HTML/JavaScript interaction
---------------------------

The following conventions are used for relating JavaScript and HTML:

Apart from the ``ONLOAD`` attribute on ``BODY``, the HTML code (as it appears
when sent to the client) contains no references to JavaScript.  Whenever some
reference from HTML elements to JavaScript is needed (for example a function
call in an ``ONCLICK`` attribute), it is the JavaScript's responsibility to
set this up by modifying the DOM.

Much of the JavaScript code does, however, expect certain elements to
be present in the HTML code.  The elements are generally adressed by
id.  To avoid very tight connections between the JavaScript and HTML,
a JavaScript object which need to access an HTML element generally
takes the id of the element as argument instead of having it hardcoded.
JavaScript object which access several related HTML elements usually
take a string used as common prefix for all ids as argument, and have
the remaining parts hardcoded.  This strategy is used in
``TimeNavigator``, ``Calendar`` and ``PositionControl``.




Problems/Future work
====================


Performance
-----------

On the test system and test data used, generating the
``/geomap/[variant]/data`` resource takes some time.  In the best cases,
it takes one or a few seconds; in the worst, up to a minute.

The major cause (by far) of the long processing time is reading of RRD
files.  As discussed in the `Server`_ section above, we cache values
from RRD files.  This is the reason why the time varies a lot (the
worst cases of time usage occur only with empty cache).

When moving or zooming the map, the new position will normally include
much of the same data as the previous, so most of the needed RRD data
will be in the cache, giving a "best case" processing time.  When
changing time interval or when first opening the map, on the other
hand, the data is usually not in cache, giving a "worst case"
processing time.

To improve the "best case" time, it is necessary to improve either the
database queries or the Python code, or both.  The *very* limited
profiling which has been performed suggests that both the database
queries and the subsequent processing of the results are responsible
for their fair share of the total processing time.  No "optimization"
has been done on the Python code (although the programmer has tried to
avoid extremely inefficient solutions), so there is probably some
potential for performance improvement here.  The database queries are
large and hairy beasts (and will probably bite you if you appear
threatening); whether (and if so, how) they can be made more efficient
is hard to say.

To improve the "worst case", the load data must simply be made
available in a different form than RRD files so that it can be read
faster.


Integration with Netmap
-----------------------

Some ideas for integration between Geomap and Netmap:

Link from Geomap to Netmap
~~~~~~~~~~~~~~~~~~~~~~~~~~~
It should be relatively easy to add a ``bbox`` argument (with the same
format as Geomap's ``bbox`` argument, see above) to Netmap and make it
show only things that are inside the specified area.  This could
either be implemented in the Netmap client, in which case the server
would have to include geographical coordinates in the GraphML document
it produces; or on the server, in which case the client would have to
forward the bbox argument to the server.

If Netmap had such an argument, one could add a link in Geomap for
showing the currently displayed area in Netmap.  The way to do this
would be to listen on the map's ``moveend`` event to update the link
each time the map is moved, and call ``getExtent()`` on the map to get the
bounds to use in the link.
(See https://openlayers.org/en/latest/apidoc/)


Link from Netmap to Geomap.
~~~~~~~~~~~~~~~~~~~~~~~~~~~
If Netmap could somehow produce a geographical bounding box for the
part of the topology the user has zoomed in on, it could create a link
to the same area in Geomap.  This may however in many cases not give
very interesting results, since netboxes that are very far apart
geographically may be close to each other in Netmap.

A different strategy could be to create a link to Geomap for each
netbox shown in Netmap (similar to the «View in IP Device Info» link).
This link could go to a Geomap page with the map centered on the
selected box and the zoom level chosen by some reasonable heuristic.
For example, the zoom level could be chosen such that all direct
neighbors of the netbox in Netmap's graph are visible.

If Netmap's GraphML data document is extended to include geographical
coordinates, both of these strategies can be implemented in the Netmap
client by computing a bounding box and using it as the ``bbox`` argument
to Geomap (see descriptions of query string parameters above).


Default configuration
---------------------

The popup boxes in the "normal" variant currently contain simple
listings of all properties.  This is convenient as an example of which
properties are available and how to get at them, but probably far from
ideal for actual use.  Better defaults should be provided based on
what users actually want to see.


Various small issues
--------------------

* Geomap is tested almost exclusively in Firefox 3 on Ubuntu (it looks like it
  is working in Opera 9 on Ubuntu too).  Since there is a lot of JavaScript
  code here, there is great potential for differences between browsers.  It
  would probably be a good idea to do some testing in more browsers.

* If (when) the server, for some reason, fails in generating the data
  resource, the network information simply disappears from the map,
  with no error message given to the user.  This is probably not
  ideal, although users may not be very interested in hearing that a
  "GargleException occured on line 42 of obscurities.py" either.  For
  development, the Web Developer Tools in either Firefox or Chrome are
  very convenient -- its console lists all the URLs requested by the
  script, so it is easy to follow the last one in order to see what the
  server said.

* When loading the Geomap page, then waiting for a long time without
  doing anything, the `next` and `last` buttons in the time selection
  remain disabled, even though the next time interval should be
  selectable (to be able to select a newer time interval, one must
  first change the time selection, for example by going one step back
  or up).  This could be fixed by using JavaScript's ``setTimeout``
  function to update the user interface regularly.

* If some users are interested in always seeing the newest data, it
  could be useful to have a `most recent data` selection as an
  alternative to selecting a specific time interval.  When this
  selection is activated, the data could be updated regularly even
  when the map is not moved (use ``setTimeout``).  Implementing this is a
  small matter of JavaScript programming.

* When zooming far out, the network data has a tendency to disappear
  completely.  This is probably caused by the fact that longitudes
  wrap around, so when the width of the map area is close to a
  multiple of the width of the whole world map, the difference between
  the longitude at the left and right edge is approximately zero.
  This confuses the code which filters out things that are outside the
  viewing area.  It should not be very difficult to come up with a
  hack to fix this.

* The :py:func:`utils.fix` function has a known error (conveniently, none of
  the actual calls to the function cause this error to occur) marked with a
  `TODO` comment.  It should probably be fixed.  (No, the function is, despite
  the name, able to fix itself.  Not in that sense, at least).



.. _OpenLayers: http://openlayers.org/
.. _OpenStreetMap: http://openstreetmap.org/
.. _OpenSearch Geo extension: https://web.archive.org/web/20180427065533/http://www.opensearch.org/Specifications/OpenSearch/Extensions/Geo/1.0/Draft_2#The_.22box.22_parameter
.. _Github: https://github.com/dewitt/opensearch/blob/master/mediawiki/Specifications/OpenSearch/Extensions/Geo/1.0/Draft%202.wiki
.. _rrdfetch: http://oss.oetiker.ch/rrdtool/doc/rrdfetch.en.html
.. _Proj4js: http://proj4js.org/
.. _Core JavaScript Reference: https://developer.mozilla.org/en/Core_JavaScript_1.5_Reference
