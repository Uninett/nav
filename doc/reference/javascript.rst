=======================================
Javascript hacking
=======================================

When writing JavaScript code try to focus on modules & not pages. In short:
follow the `module pattern
<http://www.adequatelygood.com/JavaScript-Module-Pattern-In-Depth.html>`_.

If the code is html-related, it should take selectors or objects as input and concern
itself solely about those. This makes for much easier testing and reuse. And of
course - write the tests first.

When the module is done you write a controller for the page that plugs the
needed plugins to the page elements. This should fail gracefully if the needed
elements are not present.

When we're mentioning ``module``, we do mean to follow the ``AMD``-principle
which uses the `module pattern
<http://www.adequatelygood.com/JavaScript-Module-Pattern-In-Depth.html>`_.
See `here <http://requirejs.org/docs/whyamd.html>`_ and `here
<https://github.com/amdjs/amdjs-api/wiki/AMD>`_ if your not familiar with AMD
(Asynchronous Module Definition). 

NAVs JavaScript uses :file:`media/js/libs/require.js` for loading modules and to
specify it's dependencies.

Avoiding caching
----------------

We highly suggest you create :file:`media/js/require_config.dev.js` and enable
Django debug in :file:`etc/nav.conf` when developing.

Make sure to put this in your configuration file::

  require.urlArgs = "bust=" +  (new Date()).getTime();

This makes sure your ``not using`` cached resources in your browser when
developing, which browsers loves to do! See **config-urlArgs** in `requirejs
documentation <http://requirejs.org/docs/api.html#config-urlArgs>`_ for
details.

The :file:`media/js/require_config.dev.js` is added in global HG ignore.


Handling resources requiring authentication
-------------------------------------------

As your authenticated session might have timed out due to idle (no activity),
resources will return wrong HTTP response code if you do not supply the
important X-NAV-AJAX header in your ajax requests.

This can easily be done by making sure your calling::

  NAV.addGlobalAjaxHandlers()

which is put in the global ``NAV``-namespace by :file:`media/js/default.js`


Javascript testing
==================

We're using :file:`media/js/libs/buster.js` (http://busterjs.org) for testing.
See :file:`media/js/test/*` for examples on how to write tests with busterjs.

Javascript hierarchy layout
===========================

JavaScript sources is placed under :file:`media/js/` under NAVs SCM root.

In the root (:file:`media/js/`) there should only be global configuration files
for `requirejs`, `jshint` etc!

::

  extras/
  geomap/
  libs/
  resources/
  src/
  test/

:file:`media/js/extras/` contains special dependencies/tools that is useful for
JavaScript hacking which necessary isn't JavaScript. As of this writing there
is ``downloadify`` which adds support for a **save as dialog** for asynchronous
download requests done by JavaScript.

:file:`media/js/geomap/` contains JavaScript files related to geomap module in
NAV.

:file:`media/js/libs/` contains libraries (both ``AMD`` and ``non-AMD``
libraries) which we use in NAV. ``Make sure`` you add the JavaScript as a shimmed
library in :file:`media/js/require_config.*.js` **if it is not** an ``AMD``
library.

:file:`media/js/resources/` contains resources that should be available under
buster.js testing environment. :file:`media/js/resources/libs/text.js` is such
a module which requires to be available in such an environment to do tests with
templates that gets loaded with the ``AMD``-pattern.

:file:`media/js/src/` contains our own written modules which follows the
:file:`media/js/require.js` syntax for loading modules.

:file:`media/js/src/netmap/` is the ``netmap`` backbone application.

:file:`media/js/src/plugins/` is plugins which does a particular job and only
that.

Hacking with `Backbone <http://backbonejs.org>`_
================================================

We recommend following the ``MVC/MVP``-principle (`read this for details
<http://addyosmani.github.io/backbone-fundamentals/#mvp-or-mvc>`_) when
hacking with Backbone.

Key objects to know about in Backbone:

* Model

* Collection containg a list of Model's

* View's containg a Model or a Collection (or other properties passed as
  options under the constructor/initialize.

* Router (Backbone's version of ``urls.py`` namespace.)

It's recommended you simply `read <http://backbonejs.org/>`_ the nice
documentation over at Backbone as well as trying to follow our guidelines below.
Another really useful resource is the `Backbone Fundamentals book
<http://addyosmani.github.io/backbone-fundamentals/>`_

.. _backbone_application_flow:

Backbone Application flow
-------------------------

Views ``accessing and sharing`` the same **instance of model/collection** from
:ref:`Backbone Resources` uses the ``events`` `(doc)
<http://backbonejs.org/#View-delegateEvents>`_ keymap defined in views for
reacting on changes. 

Other views ``not sharing`` the same **model/collection instance** should use
``Backbone.EventBroker`` `(doc)
<https://github.com/efeminella/backbone-eventbroker>`_ to **trigger**
notifications for data which is required else where. Views can attach an
**interests** hashmap in it's view for listning to certain **trigger**. 

**TODO**: Write about ENTRY POINT and Router and HTML5 history and blubblubbb!

.. _Backbone Resources:

Backbone Resources
------------------

We ``suggest`` you introduce a ``shared resource instance`` for sharing a single
instance of **fundemental resources** in your JavaScript application.

These resources should be able to be easily **bootstraped**
(:ref:`BackboneBootstrapping`) by the ``base HTML template``. This is also known as
a `Single-Page application
<http://en.wikipedia.org/wiki/Single-page_application>`_. 

See :ref:`BackboneTemplates` for how to work with templates and
:ref:`BackBoneBootstrapping` for how to bootstrap data.

Views `should` load it's required resources from the ``shared resource
instance`` by using your defined getter functions for retreiving `fundemental
resources`. 

You `may` pass resources with **this.options** hashmap in the view's contructor,
but be aware of the ``scary`` depedency injection that easily turns your
JavaScript application into a mess. Using this approach requires you to
**trigger** signals with ``Backbone.EventBroker`` and catching them in relevant
views with **interests** hashmap!

Backbone.EventBroker is `required` if you ``need`` **cross-application** or
**cross-modules** (ie: from different backbone applications) to communicate with
each other. This because it doesn't make sense to have a ``shared resource
instance`` between cross-application / cross-modules. ``shared resource instance``
fits only for a given/particular backbone application. 


.. _BackboneBootstrapping:

Backbone Bootstrapping
----------------------

Bootstrapping data `must` be done in the **base HTML template**.

We ``suggest`` you **prefix** your **DOM-element(s)** with
``applicationName_bootstrap_`` and `relevant name` for what you are
bootstrapping.

Example from Netmap application:

A list over saved **mapProperties** is bootstrapped under
**#netmap_bootstrap_mapPropertiesCollection** which is a `Collection
<http://backbonejs.org/#Collection>`_ of mapProperties that is used for
**toggling** between user's saved ``mapProperties (views in Netmap)``.

.. _BackboneTemplates:

Backbone Templates
------------------

We ``suggest`` to use :file:`/media/js/libs/handlebars.js` for working with
views (MVC/MVP) in JavaScript. `Handlebars.js <http://handlebarsjs.com>`_ is a
logicless templating system for making **semantic templates**

As in logicless templating system we mean that it ``only supports`` simple **for
loops**, **if**, **unless** and rendering of **context variables** given to
Handlebars. This makes templates easily to modify and work with, without
unnecessary and complex logic that shouldn't take place in views.

Handlebars homepage has a quick `introduction <http://handlebarsjs.com/>`_ for
how to use Handlebars.

For more complex functionality, Handlebars supports for **registering** helpers.
This is useful in certain situations.

**Example**
  **Context** contains a **list of persons's first names and last names**. A
  helper for directly printing the ``fullName`` given the **firstName** and
  **lastName** in the **context** would be useful.  Maybe it's also useful to
  have a helper to always ``lowerCase`` the data in given **context variable**.

  ``Please`` do remember that **views (MVC/MVP)** should contain as little
  «*logic*» as possible! It's the **controllers** job to work with the data.

Templates ``should`` be stored with the **.html** suffix in the **applications
view folder**. You ``should`` also store the template in same **hierarchy
layout** as where the Backbone.View is saved.

::

    |/media/js/src/BackboneApplicationName
    |
    |- ./views/widget/vlan.js
    |- ...
    |- ./templates/widget/vlan.html

See :ref:`BackboneLayout` for an example of how the **layout** ``should`` be done. 

.. _BackboneLayout:

Backbone Layout:
----------------

We ``suggest`` to use this following **layout** to `structurize` your Backbone
application:

::

    PWD: /media/js/src/BackboneApplicationName
    |./
    |./collections/* (for your collections)
    |./models/* (for your models used in your collections) 
    |./views/
    |./views/widgets/*
    |./views/modals/* 
    |./templates/
    |./templates/widgets/*
    |./templates/modals/* 
    | … 

/views can also be structured in more logical sections according to what your
application does if that's more natural. Just keep in mind that **widgets** and
**modals** keywords are «`reserved`».

Widgets are reusable «`mini`» components that can be used in multiple placed
cross views.

Modals are known to be «`popup` views» ref. jQuery land.


Things you shouldn't do when hacking with Backbone
--------------------------------------------------

* Dependency injection will turn your Javascript application into a mess. One
  of the strong sides with using Backbone is it's declarative event handling! 

* View's shouldn't modiy contents outside their given `DOM-element
  <http://backbonejs.org/#View-el>`_. (MVC/MVP…)
