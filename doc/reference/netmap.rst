Netmap 
======

Netmap is a topological weather map and representation of ``NAV``'s knowledge
about your network topology. 

``Before`` you continune reading this techinical documentation, ``we highly
suggest`` you read the :doc:`/reference/javascript` introduction as Netmap is a
``Javascript Application`` written in `Backbone <http://backbonejs.org>`_ and `D3JS
<http://d3js.org/>`_ with `handlebars <http://handlebarsjs.com/>`_ handling
templates with JavaScript.

Please see :ref:`API` for how topology data is fetched.

Netmap is located in :file:`/media/js/src/netmap` and bootstraped with
`requirejs` from :file:`/media/js/src/netmap/main.js` which initializes the
application (:file:`/media/js/src/netmap/app.js`).

.. _Bootstrap:

Bootstrapping
-------------

:file:`/media/js/src/netmap/main.js` does a few things when we're bootstrapping
the application:

* Doing a `sanity test for Internet Explorer` to make sure it supports the
  required features we're using (SVG!). This includes checking for **required
  IE version** and if **DocumentMode is enabled** in the browser. Particular
  the last setting might be disabled by system administrators and can be
  confusing for user's to understand why Netmap doesn't work as inteded as
  DocumentMode is required for SVG support. That's why we do the sanity test so
  we can ``inform the user``. 

* Initializing the application ``shared resources`` which is **bootstrapped**
  in backbone template :file:`/templates/netmap/backbone.html`.  (from django
  :file:`/python/nav/web/netmap` (**urls.py**, **views.py**)). See :ref:`Resources`

* Global Netmap application configuration 
  
* Registering of ``Handlebars helpers`` (todo: refactor into it's own requirejs
  dependency)

* Starting the ``router`` (takes care of HTML5 history) and loading rest of the
  application

Application flow
----------------

Views `accessing and sharing` the same **model/collection** from
:ref:`Resources` uses the ``events`` `(doc)
<http://backbonejs.org/#View-delegateEvents>`_ keymap defined in views for
reacting on changes. Other views not sharing the same model/collection instance
should use ``Backbone.EventBroker`` `(doc)
<https://github.com/efeminella/backbone-eventbroker>`_ to **trigger**
notifications for data which is required else where. Views can attach an
**interests** hashmap in it's view for listening to a certain **trigger**.

See :doc:`javascript` section :ref:`backbone_application_flow` for a more
detailed introduction!

Application views 
-----------------

Netmap has **3 main views**, each one for it's own section in the layout. These
sections are as follow:

* :ref:`NavigationView` (the **left** side,
  :file:`/media/js/src/netmap/views/navigation.js`)
 
* :ref:`DrawNetmapView` (D3JS topology graph in **center**,
  :file:`/media/js/src/netmap/views/draw_map.js`)
 
* :ref:`InfoView` (the **right** side, *
  :file:`/media/js/src/netmap/views/info.js`)

These three main views renders quite a few subviews which we call `widgets`.
The main views also has the responsibility for plugging in
:file:`/media/js/src/plugins/header_footer_minimize.js` which adds
functionaility for toggling hiding of sideviews (:ref:`NavigationView` &
:ref:`InfoView`) and NAV's header (``css: #header``).

.. _NavigationView: 

NavigationView
^^^^^^^^^^^^^^

NavigationView contains the configuration widgets for:

``Layer`` :file:`/media/js/src/netmap/views/layer_toggler.js`

  ``Layer`` widget allows the user to change between network topology
  presentation in the `OSI model <http://en.wikipedia.org/wiki/OSI_model>`_. 

  State is stored in ``activeMapProperties``, also see :ref:`Resources`.


``Categories`` :file:`/media/js/src/netmap/views/categories_toggler.js`

  ``Categories`` widget allows the user to filter between categories added in
  NAV for which categories should be included in the :ref:`DrawNetmapView`
  topology rendering. 

  State is stored in ``activeMapProperties``, also see :ref:`Resources`.

``Orphans filter`` :file:`/media/js/src/netmap/views/orphans_toggler.js`
 
 ``Orphans filter`` widget allows the user to toggle if single instance nodes
 (not being a neighbor with any other netbox in the topology graph) or not.
 This also triggers ``updateRenderCategories`` function in
 :ref:`DrawNetmapView`.

 State is stored in ``activeMapProperties``, also see :ref:`Resources`.

``Position marker`` :file:`/media/js/src/netmap/views/position_toggler.js`
  
  ``Position marker`` widget has the ability for rendering a marker around
  netboxes which are located in either the same **room** or same **location**. 

  State is stored in ``activeMapProperties``, also see :ref:`Resources`.

``Force-Algorithm`` :file:`/media/js/src/netmap/views/algorithm_toggler.js`

  ``Force-Algorithm`` widget contains controll for controlling the `D3JS force
  <https://github.com/mbostock/d3/wiki/Force-Layout>`_. As of now you can
  **pause** the topology graph or **fix** or **unfix** the **positions of all
  nodes**. It also displays a status indicator if the force algorithm is
  running or not. 

  Positions in topology graph is saved in ``GraphModel``
  :file:`/media/js/src/netmap/models/graph`, see :ref:`TopologyGraph` for more
  details.

``Topology errors``
:file:`/media/js/src/netmap/views/topology_error_toggler.js`

 ``Topology errors`` widget allows the user to control if topology errors
 detection should be rendered, like unmatched link speed of interfaces between
 the netboxes in :ref:`DrawNetmapView`. This is work in progress and later all
 the topology errors functions should be documented here.

``Mouseover`` :file:`/media/js/src/netmap/views/mouseover_toggler.js`

 Mouseover widget enables a UI-option for «auto clicking» a **netbox** or
 **link** when hovering it in the topology graph (:ref:`DrawNetmapView`).

``Traffic gradient`` :file:`/media/js/src/netmap/views/navigation.js` 

  Currenlty no widget. It renders a button and adds a event listner which calls
  ``onTrafficGradientClick``. This function basically fetches color mapping
  scheme defined by an API call (see :ref:`API_TrafficLoad`) and renders a
  modal done by :file:`/media/js/src/netmap/views/modal/traffic_gradient.js`.


.. _DrawNetmapView:

DrawNetmapView
^^^^^^^^^^^^^^

It's job is to a render a topology graph using `D3JS Force-directed graph
layout <https://github.com/mbostock/d3/wiki/Force-Layout>`_.

The topology graph includes traffic/link-load metadata in the graph. If
fetching a topology graph related to an **activeMapProperty** it might include
``metadata for netbox positions`` in the graph. 

Network Topology with traffic data get's refreshed every X-minutes. See
:ref:`API_TopologyGraph` for details about how topology data is fetched.


.. _InfoView:

InfoView
^^^^^^^^

InfoView contains the configuration widget for:

``ListMapPropertiesView`` :file:`/media/js/src/netmap/views/list_maps.js`

 It's job is to ``render available saved mapProperties (user's views)`` and let
 the user **toggle** between the views, **updating** and **saving new** views. 
  
 Saving a new view will ``popup`` the modal
 (:file:`/media/js/src/netmap/views/modal/save_new_map.js`) which contains the
 business logic for saving ``activeMapProperties``.

 Saved ``activeMapProperties`` is pr. today:

 * Selected toplogy layer to fetch topology graph for
  
 * Selected categories (gsw,gs,sw…) to render in topology graph
   
 * Orphans filter Fixed positions for netboxes in the topology graph (this
   excludes netboxes of the type ELINK's!) as ELINK is not a valid category in
   NAV yet…

``MapInfoView`` :file:`/media/js/src/netmap/views/map_info.js`
 
 It's job is to render required views/information which is related to actions
 done in :ref:`DrawNetmapView`. 

 We currently are rendering information about **selected netbox/node** or
 **selected link** in the following widgets:
  
 * NodeInfoView
  
 * LinkInfoView

 These two widgets also renders the
 :file:`/media/js/src/netmap/views/info/vlan.js` which ``lists available
 VLANs`` and has business logic for telling :ref:`DrawNetmapView` to render the
 **selected VLAN** in our topology map. 

.. _Resources:

Resources
---------

:file:`/media/js/src/netmap/resource.js` is acting as an ``internal application
state storage``.

Resources is :ref:`Bootstrap` from :file:`/media/js/src/netmap/app.js` which
makes sure to initalize the ``Resources``. Resources fetches saved
``mapProperties`` from ``#netmap_bootstrap_mapPropertiesCollection``. If
:ref:`bootstrap` also contains data for current `favorite mapProperties(view)`,
this get's updated for it's related ``activeMapProperties`` in the
``mapProperties`` collection. 

If a View requires access to data stored in ``activeMapProperties``, it
`should` fetch the active map properties by **getMapProperties**.

Router (:file:`/media/js/src/netmap/router.js`) makes sure to call
**setViewId** which basically makes sure to swap the ``activeMapProperties``
when using the `router's navigation <http://backbonejs.org/#Router-navigate>`_
function in Backbone. 


.. _TopologyGraph:

TopologyGraph
-------------

We use NAV internal topology builder (:file:`/python/nav/topology/vlans.py`) to
build a basic NetworkX topology graph and data goes thru
:file:`/python/nav/netmap/topology.py` to extend the NetworkX topology graph
with metadata from :file:`/python/nav/netmap/metadata.py` and
:file:`/python/nav/netmap/rrd.py`. 


.. _API:

API
---

Available «views» are mapped in :file:`/python/nav/web/netmap/urls.py` under
the ``api/`` prefix. Currently it only returns data as ``application/json``.

See :ref:`TopologyGraph` section above for details about how the topology is
crafted. 

See below for data you are able to fetch via API:

.. _API_TopologyGraph:

API: TopologyGraph
^^^^^^^^^^^^^^^^^^

* **api/graph/layer2$** returns a topology graph representation of ``layer 2``
  in the OSI model with traffic/link-load metadata attached to it. 

* **api/graph/layer2/<viewId>$** Same as above, only it will include metadata
  for netbox positions if there is any fixed positions saved. 

* **api/graph/layer3$** returns a topology graph representation of ``layer 3``
  in the OSI model with traffic/link-load metadata attached to it. 

* **api/graph/layer3/<viewId>$** Same as above, only it will include metadata
  for netbox positions if there is any fixed positions saved.

Example of layer2 JSON representation:

::

    {
    "nodes": [
        {
            "data": {
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
            "group": 0,
            "name": "lab-nonexistent-gw4.example.com"
        },
        {
            "data": {
                "ip": "192.168.20.3",
                "vlans": null,
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
            },
            "group": 0,
            "name": "lab-nonexistent-gw2.example.com"
        },
        # Multiple more nodes....
        # ...
        # ...
    }], // nodes
    "links": [
        {
            "source": "lab-nonexistent-gw4.example.com",
            "data": {
                "tip_inspect_link": false,
                "link_speed": 10000,
                "traffic": {
                    "outOctets": null,
                    "inOctets_css": [
                        211,
                        211,
                        211
                    ],
                    "outOctets_css": [
                        211,
                        211,
                        211
                    ],
                    "outOctetsPercentBySpeed": null,
                    "inOctets": null,
                    "inOctetsPercentBySpeed": null
                },
                "uplink": {
                    "thiss": {
                        "interface": "xe-0/0/1",
                        "netbox": "lab-nonexistent-gw4.example.com",
                        "netbox_link": "/ipdevinfo/lab-nonexistent-gw4.example.com/",
                        "interface_link": "/ipdevinfo/lab-nonexistent-gw4.example.com/interface=2891/"
                    },
                    "other": {
                        "interface": "xe-0/0/2",
                        "netbox": "rockj-gw2.example.com",
                        "netbox_link": "/ipdevinfo/rockj-gw2.example.com/",
                        "interface_link": "/ipdevinfo/rockj-gw2.example.com/interface=2535/"
                    }
                }
            },
            "target": "rockj-gw2.example.com",
            "value": 1
        },
        {
            "source": "lab-nonexistent-gw4.example.com",
            "data": {
                "tip_inspect_link": false,
                "link_speed": 100,
                "traffic": {
                    "outOctets": {
                    "raw": 0,
                    "name": "ds1",
                    "description": "ifHCOutOctets"
                    },
                    "inOctets_css": [
                        211,
                        211,
                        211
                    ],
                    "outOctetsPercentBySpeed": null,
                    "outOctets_css": [
                        211,
                        211,
                        211
                    ],
                    "inOctets": {
                        "raw": 0,
                        "name": "ds0",
                        "description": "ifHCInOctets"
                    },
                    "ifHCInOctets": {
                        "raw": 0,
                        "name": "ds0",
                        "description": "ifHCInOctets"
                    },
                    "inOctetsPercentBySpeed": null,
                    "ifHCOutOctets": {
                        "raw": 0,
                        "name": "ds1",
                        "description": "ifHCOutOctets"
                    }
                },
                "uplink": {
                    "thiss": {
                        "interface": "Fa0/1",
                        "netbox": "techserver-sw.example.com",
                        "netbox_link": "/ipdevinfo/techserver-sw.example.com/",
                        "interface_link": "/ipdevinfo/techserver-sw.example.com/interface=9303/"
                    },
                    "other": {
                        "interface": "N/A",
                        "netbox": "N/A"
                    }
                }
            },
            "target": "techserver-sw.example.com",
            "value": 1
        },
    
        # Multiple more links... (edges in graph)
        # ...
        # ...
    ] # /links
    }

.. _API_MapProperties:

API: MapProperties
^^^^^^^^^^^^^^^^^^

* **api/netmap$** returns a collection over ``mapProperties`` which is used for
  toggling between saved ``mapProperties`` (views)

* **api/netmap/defaultview$** * returns the ``viewId`` (id for a mapProperties)
  for the global favorite * ``mapProperties`` if administrator has set one.

* **api/netmap/defaultview/user$** returns the ``viewId`` for user's favorite *
  ``mapProperties`` if user has one.

Example of a saved view that tells it to load a **layer2** graph, and it's view
is ``available`` for everyone since **it is public** and has the ``categories``: **SW**,
**OTHER** and **ELINK** checked and ``visible`` in the view.
::

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

* **api/traffic_load_gradient$** List of RGB values to ranging from 0 to
  100% to be used for displaying link load. List[index] gives RGB values for
  index%.

::

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

    # for 0 and up to 100 (for every percent)
