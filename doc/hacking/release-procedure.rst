=========================================
Checklist for releasing a new NAV version
=========================================

.. highlight:: sh

CI status check
---------------

* Verify that the Jenkins jobs (at https://ci.nav.uninett.no/) related to the
  current stable branch are all green.
* If any tests are failing, these must be resolved before moving forward.


Review milestone for next release on GitHub
-------------------------------------------

* Check the list of issues targeted to the upcoming milestone at
  https://github.com/UNINETT/nav/milestones .
* Are all the targeted bugs closed?

  * Please remember that the series branch must be merged to ``master`` for
    the related issues to be automatically closed by GitHub.

* Unless any unfixed issues are showstoppers, untarget them from this milestone
  to remove clutter.

Getting the code
----------------

* Start by cloning the latest stable branch (or use ``git fetch; git checkout
  4.6.x`` to update your existing clone), e.g. 4.6.x::

    git clone -b 4.6.x git@github.com:UNINETT/nav.git
    cd nav


Updating changelog and release notes
------------------------------------

* Generate a list of referenced issues from the changelog since the last
  release::

    git log <LASTRELEASE>.. | ./tools/buglog.py

* Add a new entry to the CHANGES file for for the new release and paste the
  list produced by the above command.

* Verify that all the issues in this list are in the list of bugs targeted to
  the milestone, and vice versa.  Any differences need to be
  resolved manually.

* Once the CHANGES file has been properly updated, commit it, tag and sign the new
  release and push changes back to the official repository::

    git commit -m 'Update changelog for the upcoming X.Y.Z release'
    git tag -as X.Y.Z
    git push --tags


Rolling and uploading a new distribution tarball
------------------------------------------------

* Create a distribution tarball and sign it::

    ./dist.sh

* Draft a new release for the new tag at GitHub. Upload the tarball and the
  detached signature to the GitHub release page.

Announcing the release
----------------------

* Add a new release entry in the homepage admin panel at
  https://nav.uninett.no/admin
* Change the topic of the #nav freenode IRC channel to reference the new
  release + GitHub URL.
* Send email announcement to nav-users. Use previous release announcements as
  your template.
