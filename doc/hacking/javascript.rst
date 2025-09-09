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

CSRF Token Handling
===================

When making AJAX requests that modify data (POST, PUT, DELETE), you must include Django's CSRF token for security.

Getting the CSRF Token
-----------------------

**Method 1: From a hidden form (Recommended)**

.. code-block:: javascript

   const csrfToken = $('#some-form-id input[name="csrfmiddlewaretoken"]').val();

**Method 2: From any form on the page**

.. code-block:: javascript

   const csrfToken = $('[name=csrfmiddlewaretoken]').val();

Using CSRF Tokens in AJAX Requests
-----------------------------------

There are three ways to include a CSRF Token in the requests.

**Method 1: With jQuery POST data object:**

This method includes the CSRF token directly in the POST data. This is the most straightforward approach when you have simple form data.

.. code-block:: javascript

   $.post({
       url: '/some/endpoint/',
       data: {
           'field': 'value',
           'csrfmiddlewaretoken': csrfToken
       }
   });

**Method 2: With jQuery headers:**

This method sends the CSRF token in the HTTP headers using Django's expected header name. This is useful when posting complex data like FormData objects or JSON.

.. code-block:: javascript

   $.post({
       url: '/some/endpoint/',
       data: formData,
       headers: {
           'X-CSRFToken': csrfToken
       }
   });

**Method 3: With serialized form data:**

This method does not require getting the token from the template explicitly, but is done as part of native HTML form processing. The CSRF token is automatically included when the form is serialized.

.. code-block:: javascript

   // If posting a complete form, the token is included automatically
   $.post(url, $('#my-form').serialize());

Including CSRF Token in Templates
----------------------------------

Django templates provide the ``{% csrf_token %}`` template tag to automatically include the CSRF token in forms. This is the recommended approach for standard form submissions.

**Basic form with CSRF token:**

This is the most common pattern for regular form submissions. The CSRF token is included automatically when the form is submitted normally.

.. code-block:: html

   <form method="post" action="{% url 'some-endpoint' %}">
       {% csrf_token %}
       <input type="text" name="field_name" value="">
       <input type="submit" value="Submit">
   </form>

**Hidden form for JavaScript access:**

This pattern creates a hidden form solely to provide JavaScript access to the CSRF token. This is useful when you need to make AJAX requests from JavaScript but don't have a visible form on the page.

.. code-block:: html

   <form id="example-form" style="display: none;">
       {% csrf_token %}
   </form>

**Multiple forms on the same page:**

When you have multiple forms that perform different actions, each form needs its own CSRF token. This example shows two example forms for resource operations - one for renaming and one for deleting.

.. code-block:: html

   <form id="form-rename-resource" method="post" action="{% url 'rename-resource' resource.pk %}">
       {% csrf_token %}
       <input type="text" name="resource-name" value="{{ resource.name }}">
       <input type="submit" value="Rename resource">
   </form>

   <form id="form-delete-resource" method="post" action="{% url 'delete-resource' resource.pk %}">
       {% csrf_token %}
       <input type="submit" value="Delete resource">
   </form>

**HTMX forms with CSRF token:**

When using HTMX for dynamic content updates, the CSRF token is still required for POST requests. HTMX will automatically include the token from the form when making the request.

.. code-block:: html

   <form method="post"
         hx-post="{% url 'some-endpoint' %}"
         hx-target="#result-container">
       {% csrf_token %}
       <input type="text" name="data">
       <button type="submit">Submit</button>
   </form>

The ``{% csrf_token %}`` tag renders as a hidden input field with name ``csrfmiddlewaretoken`` that JavaScript can access to include in AJAX requests.
