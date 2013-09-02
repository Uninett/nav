==================
Javascript hacking
==================

When writing JavaScript code, try to focus on modules, not pages. In short:
follow the `module pattern
<http://www.adequatelygood.com/JavaScript-Module-Pattern-In-Depth.html>`_.

If the code is HTML-related, it should take selectors or objects as input and
concern itself solely with those. This makes for much easier testing and
reuse. And of course: Write the tests first.

When the module is done you write a controller for the page that plugs the
needed plugins to the page elements. This should fail gracefully if the needed
elements are not present.

When this documentation uses the term *module*, it refers to the
:abbr:`AMD (Asynchronous Module Definition)`
(`see API docs <https://github.com/amdjs/amdjs-api/wiki/AMD>`__) principle,
which follows the *module pattern*. NAV's JavaScript code uses
`RequireJS <http://requirejs.org/>`__ to load modules and specify their
dependencies. RequireJS provides a
`rationale for why using AMD is a good idea <http://requirejs.org/docs/whyamd.html>`__.



Avoiding caching
----------------

We highly suggest you create :file:`htdocs/js/require_config.dev.js` and enable
Django debug in :file:`etc/nav.conf` when developing.

Make sure to put this in your RequireJS configuration file:

.. code-block:: javascript

  require.urlArgs = "bust=" +  (new Date()).getTime();

This makes sure you're **not using** cached resources in your browser when
developing, something many browsers love to do! See `the RequireJS
documentation on using urlArgs <http://requirejs.org/docs/api.html#config-urlArgs>`_
for details.

The :file:`htdocs/js/require_config.dev.js` is in the global Mercurial ignore
list (file:`.hgignore`).


Handling resources that require authentication
----------------------------------------------

A user's authenticated session may expire while viewing a NAV page with
Javascript interactive elements. After a session expires,
any attempt by Javascript code to issue an AJAX request for a protected
resource on the NAV server will result in an HTTP *401 Unauthorized* response.

You can have the user be automatically sent to the login form on such an event;
make sure to initialize your Javascript app by calling:

.. code-block:: javascript

  NAV.addGlobalAjaxHandlers()

which is put in the global ``NAV`` namespace by :file:`htdocs/js/default.js`


Javascript testing
==================

We use `Karma <http://karma-runner.github.io/>`__ as our Javascript test runner.
See :file:`htdocs/js/test/*` for examples on how to write tests using Karma with
*Mocha*/*Chai*.

Javascript hierarchy layout
===========================

JavaScript sources is placed under :file:`htdocs/js/` under NAV's SCM root.

In the JavaScript root directory (:file:`htdocs/js/`) there should normally
only be global configuration files for *RequireJS*, *jshint*, etc.

::

  extras/
  geomap/
  libs/
  resources/
  src/
  test/

:file:`htdocs/js/extras/` contains special dependencies and tools that are
useful for JavaScript hacking, but which aren't necessarily implemented using
JavaScript themselves. As of this writing there is only ``downloadify``, which
adds support for a *save-as dialog* for asynchronous download requests made
from JavaScript.

:file:`htdocs/js/geomap/` contains JavaScript files related to geomap module in
NAV.

:file:`htdocs/js/libs/` contains 3rd party libraries (both *AMD* and *non-AMD*
libraries) which we use in NAV. **Make sure** you add the JavaScript as a
shimmed library in :file:`htdocs/js/require_config.*.js` **if it is not** an
*AMD* library.

:file:`htdocs/js/resources/` contains resources that should be available under
the Karma testing environment. :file:`htdocs/js/resources/libs/text.js` is such
a module which is required to be available in such an environment to run tests
with templates that get loaded using the *AMD* pattern.

:file:`htdocs/js/src/` contains the source code to NAV modules which use
*RequireJS* for dependency handling.

:file:`htdocs/js/src/netmap/` is the **Netmap** Backbone application.

:file:`htdocs/js/src/plugins/` contains re-usable JavaScript plugins.


Hacking with `Backbone <http://backbonejs.org>`__
=================================================

We recommend following the :abbr:`MVC (Model-View-Controller)` or
:abbr:`MVP (Model-View-Presenter)` principles (read the Backbone documentation
for `its take on these principles <http://addyosmani.github.io/backbone-fundamentals/#mvp-or-mvc>`_)
when hacking with Backbone.

Key objects to know about in Backbone:

* Model

* Collections containg lists of Models

* Views containg a Model or a Collection (or other properties passed as
  options under the constructor/initialization).

* Router (Backbone's equivalent of Django's :file:`urls.py` urlconf).

It's recommended you simply
`read the nice Backbone documentation <http://backbonejs.org/>`_ as well as
trying to follow our guidelines below.
Another really useful resource is the `Backbone Fundamentals book
<http://addyosmani.github.io/backbone-fundamentals/>`_

.. _backbone_application_flow:

Backbone Application flow
-------------------------

Views *accessing and sharing* the same **instance of model/collection** from
:ref:`Backbone Resources` uses the ``events`` `(doc)
<http://backbonejs.org/#View-delegateEvents>`__ keymap defined in views for
reacting on changes. 

Other views *not sharing& the same **model/collection instance** should use
``Backbone.EventBroker`` `(doc)
<https://github.com/efeminella/backbone-eventbroker>`_ to trigger
notifications for data which is required elsewhere. Views can attach an
*interests* hashmap in its view for listening to certain triggers.

.. note:: **TODO**: Write about ENTRY POINT and Router and HTML5 history and blubblubbb!

.. _Backbone Resources:

Backbone Resources
------------------

We *suggest* you introduce a *shared resource instance* for sharing a single
instance of **fundemental resources** in your JavaScript application.

These resources should be able to be easily **bootstrapped**
(:ref:`BackboneBootstrapping`) by the *base HTML template*. This is also known
as a `Single-Page application <http://en.wikipedia.org/wiki/Single-page_application>`_.

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
