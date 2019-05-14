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
================

We highly suggest you create :file:`python/nav/web/static/js/require_config.dev.js` and enable
Django debug in :file:`etc/nav.conf` when developing.

Make sure to put this in your RequireJS configuration file:

.. code-block:: javascript

  require.urlArgs = "bust=" +  (new Date()).getTime();

This makes sure you're **not using** cached resources in your browser when
developing, something many browsers love to do! See `the RequireJS
documentation on using urlArgs <http://requirejs.org/docs/api.html#config-urlArgs>`_
for details.

The :file:`python/nav/web/static/js/require_config.dev.js` is in the global Git ignore
list (file:`.gitignore`).


Javascript testing
==================

We use `Karma <http://karma-runner.github.io/>`__ as our Javascript test runner.
See :file:`python/nav/web/static/js/test/*` for examples on how to write tests using Karma with
*Mocha*/*Chai*.

Javascript hierarchy layout
===========================

JavaScript sources are placed under :file:`python/nav/web/static/js/` under NAV's SCM root.

In the JavaScript root directory (:file:`python/nav/web/static/js/`) there should normally
only be global configuration files for *RequireJS*, *jshint*, etc.

::

  python/nav/web/static/js
  |-- extras/
  |-- geomap/
  |-- libs/
  |-- resources/
  |-- src/
  `-- test/

:file:`extras/`
  contains special dependencies and tools that are
  useful for JavaScript hacking, but which aren't necessarily implemented using
  JavaScript themselves. As of this writing there is only ``downloadify``, which
  adds support for a *save-as dialog* for asynchronous download requests made
  from JavaScript.

:file:`geomap/`
  contains JavaScript files related to geomap module in NAV.

:file:`libs/`
  contains 3rd party libraries (both *AMD* and *non-AMD* libraries) which we
  use in NAV. **Make sure** you add the JavaScript as a shimmed library in
  :file:`python/nav/web/static/js/require_config.*.js` **if it is not** an *AMD* library.

:file:`resources/`
  contains resources that should be available under the Karma testing
  environment. :file:`python/nav/web/static/js/resources/libs/text.js` is such a module which
  is required to be available in such an environment to run tests with
  templates that get loaded using the *AMD* pattern.

:file:`src/`
  contains the source code to NAV modules which use *RequireJS* for dependency
  handling.

:file:`src/netmap/`
  is the **Netmap** Backbone application.

:file:`src/plugins/`
  contains re-usable JavaScript plugins.
