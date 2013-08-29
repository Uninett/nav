=======
PyCharm
=======

Activate NAV developers is privileged to have access to an open source license
for `PyCharm IDE <http://www.jetbrains.com/pycharm/>`_ by
`Jetbrains <http://www.jetbrains.com>`_.

Obtaining the open source license
---------------------------------

Contact the project leader for NAV to verify your eligible for obtaining
a copy of our open source license. As of today the project lead is Morten
Brekkevold.

Install
-------

TODO: fix a screen cast ;-)

Fetch `PyCharm <http://www.jetbrains.com/pycharm/download/index.html>`_ and
follow the instruction at their web page for installing PyCharm.

After install we assume you are using the :doc:`/howto/vagrant` setup for
installing NAV. Ensure this is done before you continue.


Running unit tests automagically on code change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In the configuration (nav-bar, left for the green RUN arrow), click edit run
configurations):

* Top left, + sign for adding a new run configuration
* Select "Python's test" and "py.test" in the tree-view on the left side bar.

Run configuration options should be the following:

* Name: NAV UNIT TESTS
* Target: $NAV-ROOT/tests/unittests
* Ensure you set correct python interpreter

Either use the `Remote python interpreter` from `vagrant` or if you have
installed the same virtualenv locally to make tests run faster.

Click save and apply.

Generate documentation
^^^^^^^^^^^^^^^^^^^^^^

In the configuration (nav-bar, left for the green RUN arrow), click edit run
configurations):

* Top left, + sign for adding a new run configuration
* Select "Python docs" and "Sphinx Task" in the tree-view on the left side bar.

Run configuration options should be the following:

* Command: html
* input: :file:`$NAV-ROOT/doc`
* output: :file:`$NAV-ROOT/doc/html`

After run you should be able to access the documentation under
:file:`$NAV-ROOT/doc/html`.