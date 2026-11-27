:diataxis: reference
:audience: developer

=========================
Writing NAV documentation
=========================

NAV's documentation has grown over many years without a common structure.
We are gradually reorganizing it according to `Diátaxis
<https://diataxis.fr/>`_, a framework for organizing technical
documentation. Most of the existing documentation does not follow it yet.

This page describes the structure we are aiming for, and what to do when you
add a new page or change an existing one, so that each change moves the
documentation a little closer to that goal. It applies to everything under
:file:`doc/`.

NAV's documentation is written in reStructuredText and built with Sphinx.
Read the Docs builds it for every pull request, and links a rendered preview
from the pull request's checks.


The four kinds of documentation
===============================

Diátaxis identifies four kinds of documentation, each serving a different
need:

.. list-table::
   :header-rows: 1
   :widths: 15 25 60

   * - Kind
     - Answers
     - Purpose
   * - Tutorial
     - "Can you teach me to...?"
     - A lesson. Takes a newcomer through a series of steps that always
       work, so they gain skill and confidence.
   * - How-to guide
     - "How do I...?"
     - Directions for a competent user who wants to reach a specific goal.
   * - Reference
     - "What is...?"
     - Accurate, complete and neutral description of the machinery: programs,
       options, configuration files, APIs, data models.
   * - Explanation
     - "Why...?"
     - Background, context and design rationale, to deepen understanding.

To decide which kind a piece of text is, ask two questions:

1. Does it inform *doing* something (action), or *knowing* something
   (cognition)?
2. Does it serve someone who is *learning* (study), or someone who is
   *getting work done* (work)?

.. list-table::
   :header-rows: 1
   :stub-columns: 1

   * -
     - Study
     - Work
   * - Action
     - Tutorial
     - How-to guide
   * - Cognition
     - Explanation
     - Reference

A common problem in documentation is mixing these kinds on the same page.
Typical examples are a reference page that wanders into a step-by-step
recipe, or a tutorial that stops to list every option. Keep each page to one
kind, and link to the other kinds instead.


Writing each kind
-----------------

Tutorials
  Write as a teacher: "In this tutorial, we will...". Pick one path and do
  not offer alternatives. Show the expected result of each step. Keep
  explanation to a sentence and a link. A tutorial must work every time for
  every reader, so test it.

How-to guides
  The title says what the guide achieves, e.g. "How to connect NAV to Active
  Directory". Assume the reader knows what they are doing. Leave out teaching
  and background. Link to the reference for the full list of options.

Reference
  Describe, and only describe. Structure the reference like the thing it
  describes, usually with one page per program, configuration file or web
  tool. Prefer reference that is generated from the code, e.g. with
  ``autodoc``, ``program-output`` or ``literalinclude`` of the shipped
  configuration files, since it cannot drift from the code.

Explanation
  The title should work with "About...", e.g. "About events and alerts".
  Discuss why things are the way they are, including history, design
  decisions and alternatives. Leave out step-by-step instructions and lists
  of options.


The structure we are aiming for
===============================

The goal is for the documentation to have two main parts, one for each
audience, with each part divided into the four kinds of documentation. Each
part and kind has its own directory under :file:`doc/`:

.. code-block:: text

   using/                Using and running NAV: users, NAV administrators
                         and operators, and integrators using the REST API
       tutorials/
       howto/            install, configure, use the web tools, use the
                         API, troubleshoot, upgrade
       reference/        web tools, command line programs, configuration
                         files, event and alert types, REST API, glossary
       explanation/      how NAV works, organizing your network data,
                         events and alerts, topology, users and
                         privileges, metrics
   developing/           Developing NAV: contributors, and authors of
                         plugins
       tutorials/
       howto/            contribute a change, change the database schema,
                         run the tests
       reference/        coding conventions, internal APIs, data models,
                         extension hooks
       explanation/      design rationale and project history

Each directory has an :file:`index.rst` landing page. The release notes stay
where they are.

Today, most pages are still organized under the older :file:`intro/`,
:file:`howto/`, :file:`reference/` and :file:`hacking/` directories, and many
of them mix several kinds of documentation. This page itself is in
:file:`hacking/`, and will move to :file:`developing/reference/` along with
the first other page that goes there.


Changing the structure gradually
================================

We are not reorganizing the documentation in one go. Instead, every change
should move it a little closer to the structure above. This follows the
`Diátaxis advice on applying it to existing documentation
<https://diataxis.fr/how-to-use-diataxis/>`_. Restructuring happens on
``master`` only. Pull requests against a stable branch (``<major>.<minor>.x``)
do not move or split pages.

When you **add a new page**:

* Decide which kind of documentation it is, and which audience it is for.
* Put it in the right place in the new structure.
* If that directory does not exist yet, create it, along with a landing page
  for it. A landing page should read like an overview: introduce what the
  section contains, instead of only listing links.
* Add the metadata fields described in `Marking a page's kind and
  audience`_.

When you **rewrite a page, or a large part of it**:

* Check whether it is in the right place. If it is not, move it as part of
  the same pull request, as described in `Moving a page`_.
* If it mixes several kinds of documentation, split out at least the part
  you are working on.
* Add the metadata fields, if the page does not have them yet.

Smaller changes, such as fixing a fact or adding an option, don't require
any of this.

In general:

* Never create empty sections in advance. A section appears when its first
  page does.
* Small improvements are welcome. Each step in the right direction is worth
  merging on its own.


Moving a page
-------------

Pages are linked from all over the internet, and from NAV itself: NAV's web
interface links to the copy of the documentation it serves under ``/doc/``.
Every page that is moved or renamed must leave a redirect behind, so that
old links keep working.

Move a page in a commit of its own, without changing its content. Git does
not record renames, but detects them when a file's content is mostly
unchanged. A commit that only moves a page keeps the page's history easy to
follow, and is easy to review. Make content changes in separate commits.

A commit that moves a page should:

1. Move the file with :command:`git mv`.
2. Update the ``toctree`` entries that list it.
3. Update everything that links to it. Search the whole repository for the
   old path without its file extension, e.g. :command:`git grep
   setting-up-logging`, not just :file:`doc/`. Links from Python code,
   templates, :file:`README.rst` and the pull request template are not
   covered by redirects.
4. Fix relative paths in ``include``, ``literalinclude``, ``image`` and
   ``figure`` directives. Paths that start with ``/`` are resolved from
   :file:`doc/`, and survive future moves.
5. Add a redirect to the ``redirects`` dictionary in :file:`doc/conf.py`. The
   key is the old page's path relative to :file:`doc/`, without ``.rst``.
   The value is the new page's URL. Start it with ``/``, so that it is
   resolved from the root of the documentation:

   .. code-block:: python

      redirects = {
          "howto/setting-up-logging": "/using/howto/logging.html",
      }

   Keep the dictionary sorted by key. If the page has been moved before,
   update the earlier redirects to point to its new location too.

After the move, check that the build gives no new warnings. Redirects are
not validated by the build, so open the old URL in the pull request's Read
the Docs preview, and check that it lands on the new page.

When you split a page, keep each ``.. _label:`` target together with the
content it labels, and search the repository for links to the old page's
section anchors (``page.html#section``). Redirects only cover whole pages,
so links to sections that moved to another page break silently.


Marking a page's kind and audience
==================================

New pages should start with two metadata fields:

.. code-block:: rst

   :diataxis: how-to
   :audience: operator

   =========================
   How to set up LDAP logins
   =========================

The fields must come before the page title. Sphinx then records them as
metadata for the page, and does not show them. If they are placed after the
title, Sphinx shows them on the page instead.

``:diataxis:``
  One of ``tutorial``, ``how-to``, ``reference``, ``explanation``,
  ``landing`` or ``mixed``. Use ``landing`` for landing pages, and
  ``mixed`` for an existing page that still needs to be split.

``:audience:``
  The page's main audience: one of ``user`` (someone using the web interface
  to monitor the network), ``operator`` (someone installing, configuring or
  administering NAV, including users and privileges, or integrating with it
  through the API) or ``developer``.

Most existing pages do not have these fields yet. To list the pages that
still need to be assessed, run::

  git grep -L '^:diataxis:' -- 'doc/*.rst'
