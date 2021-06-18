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


Updating changelog and release notes
------------------------------------

* Generate a list of referenced issues from the GitHub milestone::

    ./tools/buglog.py 4.8.3

  ``buglog`` depends on the ``github`` library, install with
  ``pip install PyGithub``.
  (`PyGithub documentation <https://pygithub.readthedocs.io/en/latest/>`_)

* Add a new entry to the CHANGES file for for the new release and paste the
  list produced by the above command. Commit the changes::

    git commit -m 'Update changelog for the upcoming X.Y.Z release'

* Bump and tag the version number (and sign the tag) using ``version.sh``, and
  push the changes back to the official repository::

    ./version.sh -t
    git push --tags


Announcing the release
----------------------

* Draft a new release for the new tag at GitHub.
* Add a new release entry in the homepage admin panel at
  https://nav.uninett.no/admin
* Change the topic of the #nav Libera.Chat IRC channel to reference the new
  release + GitHub URL.
* Send email announcement to the ``nav-users`` mailing list. Use previous
  release announcements as your template.
