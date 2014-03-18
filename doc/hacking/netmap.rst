======
Netmap
======

Netmap is a topological weather map and representation of NAV's knowledge
of your network topology.

Before you continune reading this technical reference documentation, we highly
suggest you read the :doc:`javascript` introduction.

Netmap is a JavaScript application (with a Django backend to feed it with
topology data), using `Backbone <http://backbonejs.org>`_, `D3.js
<http://d3js.org/>`_ and `Handlebars <http://handlebarsjs.com/>`_.

Please see :ref:`Netmap_API` for how topology data is fetched.

Netmap is located in :file:`htdocs/js/src/netmap/` and bootstraped with
RequireJS from :file:`htdocs/js/src/netmap/main.js`, which initializes the
application (:file:`htdocs/js/src/netmap/app.js`).

.. _Bootstrap:

Bootstrapping
-------------

:file:`htdocs/js/src/netmap/main.js` does a few things when bootstrapping the
application:

* Runs a "sanity test" for Internet Explorer to make sure it supports the
  required features we're using (:abbr:`SVG (Scalable Vector Graphics)`). This
  includes verifying the *required IE version* and that *DocumentMode is
  enabled* in the browser. 

  Particularly, the last setting is required for SVG support, but it is
  sometimes disabled by corporate system administrators, causing users to
  become confused over why Netmap isn't working properly.

* Initializes the application's *shared resources*, which is bootstrapped in
  the backbone template :file:`templates/netmap/backbone.html`. (served by
  :py:mod:`nav.web.netmap`). See :ref:`Netmap_Resources`.

* Global Netmap application configuration.
  
* Registers of Handlebars "helpers" (TODO: refactor into it's own RequireJS
  dependency)

* Starting the Backbone *router* (takes care of HTML5 history) and loading
  rest of the application.


Application flow
----------------

Views accessing and sharing the same model or collection from
:ref:`Netmap_Resources` uses the *events* `(doc)
<http://backbonejs.org/#View-delegateEvents>`__ keymap defined in views for
reacting on changes. Other views not sharing the same model/collection instance
should use ``Backbone.EventBroker`` `(doc)
<https://github.com/efeminella/backbone-eventbroker>`__ to trigger
notifications for data which is required elsewhere. A view can attach an
code:`interests` hashmap for listening to a certain trigger.

See :ref:`backbone_application_flow` for a more detailed introduction!


Application views
-----------------

Netmap has *3 main views*, one for each section in the UI layout. These
sections are as follows:

* :ref:`NavigationView` (the *left* side panel,
  :file:`htdocs/js/src/netmap/views/navigation.js`)
 
* :ref:`DrawNetmapView` (D3.js topology graph in the *center* panel,
  :file:`htdocs/js/src/netmap/views/draw_map.js`)
 
* :ref:`InfoView` (the *right* side panel,
  :file:`htdocs/js/src/netmap/views/info.js`)

These three main views render quite a few subviews, which we call *widgets*.
The main views also have the responsibility for plugging in
:file:`htdocs/js/src/plugins/header_footer_minimize.js`, which enables
toggling the visibility of the side panels (:ref:`NavigationView` &
:ref:`InfoView`) and NAV's header (``css: #header``).

.. _NavigationView: 

NavigationView
^^^^^^^^^^^^^^

NavigationView contains the configuration widgets for:

Layer (:file:`htdocs/js/src/netmap/views/layer_toggler.js`)

  The *Layer* widget allows the user to switch between which topology layers,
  either the VLAN topology map (Layer 2), or the IP topology map (Layer 3).

  State is stored in :js:data:`activeMapProperties`, also see
  :ref:`Netmap_Resources`.


Categories (:file:`htdocs/js/src/netmap/views/categories_toggler.js`)

  The *Categories* widget allows the user to filter the map contents based on
  NAV device categories.

  State is stored in :js:data:`activeMapProperties`, also see
  :ref:`Netmap_Resources`.

Orphans filter (:file:`htdocs/js/src/netmap/views/orphans_toggler.js`)
 
 The *Orphans filter* widget allows the user to toggle whether orphan nodes
 should be displayed in the map.
 This also triggers :js:func:`updateRenderCategories` function in
 :ref:`DrawNetmapView`.

 State is stored in :js:data:`activeMapProperties`, also see
 :ref:`Netmap_Resources`.

Position marker (:file:`htdocs/js/src/netmap/views/position_toggler.js`)
  
  The *Position marker* widget allows the user to mark netboxes which are
  located in either the same *room* or same *location*.

  State is stored in :js:data:`activeMapProperties`, also see
  :ref:`Netmap_Resources`.

Force-Algorithm (:file:`htdocs/js/src/netmap/views/algorithm_toggler.js`)

  The *Force-Algorithm* widget contains controls to manipulate the `D3.js
  force layout <https://github.com/mbostock/d3/wiki/Force-Layout>`_. As of
  now, you can *pause* the topology graph or *fix*/*unfix* the positions of
  all nodes. It also contains a force layout algorithm activity indicator.

  Positions in topology graph is saved in :js:class:`GraphModel`
  (:file:`htdocs/js/src/netmap/models/graph`), see :ref:`TopologyGraph` for
  more details.

Topology errors (:file:`htdocs/js/src/netmap/views/topology_error_toggler.js`)

 The *Topology errors* widget allows the user to control whether detected
 topology errors should be rendered. Typical errors include link speed
 mismatches between connected interfaces. This is work in progress and later
 all the topology errors functions should be documented here.

Mouseover (:file:`htdocs/js/src/netmap/views/mouseover_toggler.js`)

 The *Mouseover* widget contains a UI-option for "auto-selecting" a Netbox or
 a link when hovering over it in the topology graph (:ref:`DrawNetmapView`).

Traffic gradient (:file:`htdocs/js/src/netmap/views/navigation.js`)

  Currenlty no widget. It renders a button and adds an event listner which
  calls :js:func:`onTrafficGradientClick`. This function basically fetches the
  color mapping scheme defined by an API call (see :ref:`API_TrafficLoad`) and
  renders a modal done by
  :file:`htdocs/js/src/netmap/views/modal/traffic_gradient.js`.


.. _DrawNetmapView:

DrawNetmapView
^^^^^^^^^^^^^^

Its job is to a render a topology graph using `D3.js force-directed graph
layout <https://github.com/mbostock/d3/wiki/Force-Layout>`_.

The topology graph includes traffic/link-load metadata. If fetching a topology
graph related to an :js:data:`activeMapProperty` it might include metadata for
netbox positions in the graph.

Network topology with traffic data is refreshed every X minutes. See
:ref:`API_TopologyGraph` for details about how topology data is fetched.


.. _InfoView:

InfoView
^^^^^^^^

InfoView contains the configuration widget for:

ListMapPropertiesView (:file:`htdocs/js/src/netmap/views/widgets/list_maps.js`)

  Its job is to render available saved :js:data:`mapProperties` (users' views)
  and let the user toggle between the views, *updating* and *saving* new views.

  Saving a new view will pop up` the modal
  (:file:`/media/js/src/netmap/views/modal/save_new_map.js`) which contains the
  UI for saving :js:data:`activeMapProperties`.

  Saved :js:data:`activeMapProperties` contains (as of this writing):

  * The selected topology layer.

  * The category filter selections.

  * The orphans filter option.

  * Fixed positions for netboxes in the topology graph

    .. note:: This excludes netboxes of the type ELINK, as ELINK is not a 
              valid category in NAV yet

MapInfoView (:file:`htdocs/js/src/netmap/views/widgets/map_info.js`)
 
  Its job is to render required views/information which is related to actions
  done in :ref:`DrawNetmapView`.

  We currently render information about the selected netbox/node or
  the selected link in the following widgets:

  * NodeInfoView

  * LinkInfoView

  These two widgets also render
  :file:`htdocs/js/src/netmap/views/info/vlan.js`, which lists available
  VLANs, and has business logic for telling :ref:`DrawNetmapView` to render the
  selected VLAN in our topology map. 

.. _Netmap_Resources:

Resources
---------

:file:`htdocs/js/src/netmap/resource.js` acts as an "internal application
state storage".

Resources are bootstrapped from :file:`htdocs/js/src/netmap/app.js`, which
makes sure to initalize the Resources. Resources fetches saved
:js:data:`mapProperties` from ``#netmap_bootstrap_mapPropertiesCollection``.

If :ref:`bootstrap` also contains data for the current favorite
``mapProperties(view)``, this gets updated for its related 
:js:data:`activeMapProperties` in the js:data:`mapProperties` collection. 

If a View requires access to data stored in :js:data:`activeMapProperties`, it
should fetch the active map properties using :js:func:`getMapProperties`.

The Router (:file:`htdocs/js/src/netmap/router.js`) makes sure to call
:js:func:`setViewId`, which basically makes sure to swap the 
:js:data`activeMapProperties` when using the
`router's navigation <http://backbonejs.org/#Router-navigate>`_
function in Backbone. 


.. _TopologyGraph:

TopologyGraph
-------------

NAV's internal topology builder (:py:mod:`nav.topology.vlans`) is used to
build a basic *NetworkX* topology graph.
:py:mod:`nav.netmap.topology` is used to extend this NetworkX topology graph
with metadata from :py:mod:`nav.netmap.metadata` and traffic load data from
:py:mod:`nav.netmap.rrd`. 


.. _Netmap_API:

API
---

Available backend views are mapped in :py:mod:`nav.web.netmap.urls` under the
``api/`` URL prefix. Currently it only returns data as
:mimetype:`application/json`.

See :ref:`TopologyGraph` section above for details about how the topology is
crafted. 

See below for data you are able to fetch via API:

.. _API_TopologyGraph:

API: TopologyGraph
^^^^^^^^^^^^^^^^^^

These external URLs are available to retrieve map data from NAV:

``api/graph/layer2``
  returns a topology graph representation of ``layer 2`` in the OSI model with
  traffic/link-load metadata attached to it.

``api/graph/layer2/<viewId>``
  Same as above, only it will include metadata for netbox positions if there
  is any fixed positions saved.

``api/graph/layer3``
  returns a topology graph representation of ``layer 3`` in the OSI model with
  traffic/link-load metadata attached to it.

``api/graph/layer3/<viewId>``
  Same as above, only it will include metadata for netbox positions if there
  is any fixed positions saved.

Example of a layer2 JSON representation:

.. code-block:: json

    {
        "vlans": {
            "136": {
                "nav_vlan": 136,
                "net_ident": "labnett",
                "vlan": 22,
                "description": "experimental"
            },
            "139": {
                "nav_vlan": 139,
                "net_ident": "awesomeness",
                "vlan": 42,
                "description": "foo"
            }
        },
        "nodes": {
            "1": {
                "ip": "192.168.0.9",
                "vlans": null,
                "id": "1",
                "category": "GW",
                "sysname": "lab-nonexistent-gw4.example.com",
                "room": "lab-nonexistent (None)",
                "ipdevinfo_link": "/ipdevinfo/lab-nonexistent-gw4.example.com/",
                "up": "y",
                "up_image": "green.png",
                "locationid": "norge",
                "location": "Norge",
                "position": null,
                "is_elink_node": false,
                "roomid": "lab-nonexistent"
            },
            "3": {
                "ip": "192.168.20.3",
                "vlans": [
                    "nav_vlan_id",
                    "nav_vlanid"
                ],
                "id": "3",
                "category": "GW",
                "sysname": "lab-nonexistent-gw2.example.com",
                "room": "lab-nonexistent (None)",
                "ipdevinfo_link": "/ipdevinfo/lab-nonexistent-gw2.example.com/",
                "up": "y",
                "up_image": "green.png",
                "locationid": "norge",
                "location": "Norge",
                "position": null,
                "is_elink_node": false,
                "roomid": "lab-nonexistent"
            }
        },
        "links": [
            {
                "source": "1",
                "vlans": [
                    136,
                    139,
                    141
                ],
                "target": "3",
                "edges": [
                    {
                        "source": {
                            "interface": {
                                "ipdevinfo_link": "/ipdevinfo/lab-nonexistent-gw4.example.com/ifname=Gi1/31/",
                                "ifname": "Gi1/31"
                            },
                            "netbox": "1",
                            "vlans": []
                        },
                        "link_speed": 1000,
                        "vlans": [],
                        "traffic": {
                            "source": {
                                "rrd": {
                                    "raw": 940.472009,
                                    "name": "ds0",
                                    "description": "ifHCInOctets"
                                },
                                "load_in_percent": 0.0007523776072,
                                "percent_by_speed": "0.00",
                                "css": [
                                    22,
                                    255,
                                    0
                                ],
                                "name": "ifHCInOctets"
                            },
                            "target": {
                                "rrd": {
                                    "raw": 8283.235853,
                                    "name": "ds1",
                                    "description": "ifHCOutOctets"
                                },
                                "load_in_percent": 0.0066265886824,
                                "percent_by_speed": "0.01",
                                "css": [
                                    22,
                                    255,
                                    0
                                ],
                                "name": "ifHCOutOctets"
                            }
                        },
                        "target": {
                            "interface": {
                                "ipdevinfo_link": "/ipdevinfo/lab-nonexistent-gw2.example.com/ifname=Gi4/24/",
                                "ifname": "Gi4/24"
                            },
                            "netbox": "3",
                            "vlans": []
                        }
                    },
                    {
                        "source": {
                            "interface": {
                                "ipdevinfo_link": "/ipdevinfo/lab-nonexistent-gw4.example.com/ifname=Po2/",
                                "ifname": "Po2"
                            },
                            "netbox": "1",
                            "vlans": []
                        },
                        "link_speed": 3000,
                        "vlans": [
                            136,
                            139,
                            141
                        ],
                        "traffic": {
                            "source": {
                                "rrd": {
                                    "raw": 17106.277051,
                                    "name": "ds0",
                                    "description": "ifHCInOctets"
                                },
                                "load_in_percent": 0.0045616738802666664,
                                "percent_by_speed": "0.00",
                                "css": [
                                    22,
                                    255,
                                    0
                                ],
                                "name": "ifHCInOctets"
                            },
                            "target": {
                                "rrd": {
                                    "raw": 1998.513284,
                                    "name": "ds1",
                                    "description": "ifHCOutOctets"
                                },
                                "load_in_percent": 0.0005329368757333334,
                                "percent_by_speed": "0.00",
                                "css": [
                                    22,
                                    255,
                                    0
                                ],
                                "name": "ifHCOutOctets"
                            }
                        },
                        "target": {
                            "interface": {
                                "ipdevinfo_link": "/ipdevinfo/lab-nonexistent-gw2.example.com/ifname=Po2/",
                                "ifname": "Po2"
                            },
                            "netbox": "3",
                            "vlans": []
                        }
                    }
                ]
            }
        ]
    }

.. _API_MapProperties:

API: MapProperties
^^^^^^^^^^^^^^^^^^

``api/netmap``
  returns a collection of ``mapProperties`` which is used for toggling between
  saved ``mapProperties`` (views)

``api/netmap/defaultview``
  returns the ``viewId`` (id for a mapProperties) for the global favorite
  ``mapProperties``, if the administrator has set one.

``api/netmap/defaultview/user``
  returns the ``viewId`` for user's favorite ``mapProperties``, if the user
  has one.

Here is an example of a *public*, saved *layer 2* view, which includes the
categories **SW**, **OTHER** and **ELINK**:

.. code-block:: json

    {
        "display_orphans": false,
        "last_modified": "2013-03-25 10:36:29.917686",
        "description": "A longer description of the view",
        "title": "Demo view for netmap",
        "owner": 1,
        "is_public": true,
        "viewid": 6,
        "zoom": "292.55449906242416,397.7677173360468;0.18428365216138762",
        "categories": [
            "SW",
            "OTHER",
            "ELINK"
        ],
        "topology": 2
    }

.. _API_TrafficLoad:

API: No category
^^^^^^^^^^^^^^^^

``api/traffic_load_gradient``
  Returns a list of 101 RGB color values representing a load range of 0 to
  100%.  List[index] gives RGB values for index%.

.. code-block:: javascript

    [
        {
            "r": 22,
            "b": 0,
            "g": 255
        },
        {
            "r": 32,
            "b": 0,
            "g": 255
        },
        {
            "r": 47,
            "b": 0,
            "g": 255
        },
    ....
    ]

    // for 0 and up to 100 (for every percent)
