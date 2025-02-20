===============
Event Templates
===============

Event Templates are introduced to be able to display more detailed information
about a specific event. This template is included in the status details and on
the event details page.


Creating a template
===================

To create a template for an event you need to know what the **event type** and
optionally the **alert type** is.  For detail on this, please refer to
:doc:`event and alert type reference documentation <alerttypes>`.

File structure
--------------

To start using custom event templates create a directory called *templates* in
NAV's etc-directory, and inside that directory you create the *alertmsg*
directory. And finally inside this directory you can add event templates using
the following structure::

  base.html
  <event-type>
  ..base.html
  ..<alert-type>.html
  <event-type>
  ..base.html
  ..<alert-type>.html


For a boxDown template it would look like this::

  templates
  ..alertmsg
    ..boxState
      ..boxDown.html


Common template for all events
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a template common for all events, create the *base.html* and add html
there.

Common template for an event-type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a template common for for instance boxState-events, create the
directory *boxState* and the file *base.html* inside the directory and add html
there.

Single template for an alert-type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a template for all boxDown-events, you create the directory *boxState*
because that is the event-type of *boxDown* and then you create the file
*boxDown.html* and add html there.


Template editing
----------------

The templates are
Django-templates. https://docs.djangoproject.com/en/4.2/ref/templates/ . The
base-templates are optional but useful if you have common information for all
templates. To learn about template inheritance, see
https://docs.djangoproject.com/en/4.2/ref/templates/language/#template-inheritance .


Template context
----------------

The template has all the variables from the API as well as the alert-object
available. See /api/1/alert and the class `AlertHistory` in the file
`python/nav/models/event.py` for more details.


nav.models.event.AlertHistory
-----------------------------

.. autoclass:: nav.models.event.AlertHistory
   :members:
   :undoc-members:
