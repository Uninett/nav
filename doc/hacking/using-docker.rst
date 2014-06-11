=====================================
Using NAV with Docker for development
=====================================

Docker is a lightweight virtualization framework for creating isolated
environments, useful both in development and production [*]_.
For more information on Docker visit their homepage_ or read the documentation_.

.. Note:: This guide is written for NAV 4.0 or later.

Installing Docker
-----------------
Docker has updated documentation on how to install it for most linux
distributions [*]_. Due to its dependency on a relatively new kernel (3.8+),
some distributions such as Debian stable will need to use a backports kernel.

.. Tip:: To avoid having to use sudo with docker commands it is recommended
         to add your user to the **docker** group. You may need to relogin for it to
         take effect.

Building the Docker image
-------------------------
First you will need to obtain the NAV source code. The image can then be
built with the following command::

    docker build -t <IMAGE_NAME> <PATH>

Where `IMAGE_NAME` is the name you wish to give the built image and `PATH` is
the path to the NAV root directory containing the dockerfile.
    * If you are currently in the NAV root directory you need only use a **\.** for PATH.

.. Tip:: This would be the perfect time to grab some coffee (and maybe redecorate your
         living room), as this may take a while.


Creating and running the container
----------------------------------
The first time you wish to run the container it must be created with the
following command::

    docker run -v <PATH>:/source -d --name <CONTAINER_NAME> -p <HOST_PORT1>:80 -p <HOST_PORT2>:22 -p <HOST_PORT3>:8000 <IMAGE_NAME>

Where:
    * `PATH` is the path to the NAV root directory.
    * `CONTAINER_NAME` is the name you wish to give the container (optional but recommended).
    * `HOST_PORT1` is the port number on the host that should map to container port 80.
    * `HOST_PORT2` is the port number on the host that should map to container port 22.
    * `HOST_PORT3` is the port number on the host that should map to container port 8000 (Graphite web interface).
    * `IMAGE_NAME` is the name you gave the image at the previous step.

To see if the container is running execute::

    docker ps

Once the container has been created successfully you can stop|start the container with::

    docker stop|start <CONTAINER_NAME>

Happy hacking!


.. [*] Docker is currently not considered production ready.
.. [*] See http://docs.docker.io/installation/#installation.
.. _homepage: http://docker.io
.. _documentation: http://docs.docker.io