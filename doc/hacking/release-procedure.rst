=========================================
Checklist for releasing a new NAV version
=========================================

.. highlight:: sh

CI status check
---------------

* Verify that the GitHub Actions workflows (at
  https://github.com/Uninett/nav/actions ) related to the current stable branch
  are all green.
* If any tests are failing, these must be resolved before moving forward.


Review milestone for next release on GitHub
-------------------------------------------

* Check the list of issues targeted to the upcoming milestone at
  https://github.com/Uninett/nav/milestones .
* Are all the targeted bugs closed?

  * Please remember that the series branch must be merged to ``master`` for
    the related issues to be automatically closed by GitHub.

* Unless any unfixed issues are showstoppers, untarget them from this milestone
  to remove clutter.

Getting the code
----------------

* Start by cloning the latest stable branch (or use ``git fetch; git checkout
  4.8.x`` to update your existing clone), e.g. 4.8.x::

    git clone -b 4.8.x git@github.com:UNINETT/nav.git
    cd nav

Ensure generated docs are up to date
------------------------------------

Some documentation source files need to be built using a running PostgreSQL
database. If any changes have been made to the default event- and
alert-hierarchies provided by NAV, these documentation source files need to be
updated and checked into Git.

If you have a full dev environment running (such as the environment defined by
:file:`docker-compose.yml`), use the following to generate new docs and verify
whether they have changed::

    make doc
    git status

If you see files under the :file:`doc` directory were changed, these changes
need to be checked into Git to ensure the documentation is up to date for the
new release.


Updating changelog and release notes
------------------------------------

Towncrier can be used to automatically produce a changelog using the
:file:`changelog.d` directory which contains files describing changes since the last release.

To add these changes to :file:`CHANGELOG.md` simply run

.. code-block:: console

  $ towncrier build --version {version}

This will also delete all files in :file:`changelog.d/`.

To preview what the addition to the changelog file would look like add the flag
``--draft``.
A few other helpful flags are:
* `date DATE` - set the date of the release, default is today
* `keep` - keep all news fragments
  
Commit the changes using

.. code-block:: console

  $ git commit -m 'Update changelog for the upcoming X.Y.Z release'

Bump and tag the version number (and sign the tag) using ``version.sh``, and
push the changes back to the official repository:

.. code-block:: console

  $ ./version.sh -t
  $ git push --tags


Announcing the release
----------------------

* Draft a new release for the new tag at GitHub.
* Add a new release entry in the NAV homepage at
  https://github.com/Uninett/nav-landing-page/tree/master/content/releases
* Send email announcement to the ``nav-users`` mailing list. Use previous
  release announcements as your template.
