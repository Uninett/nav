#!/usr/bin/env python
# -*- testargs: --list-plugins -*-
"""
The ipdevpoll deamon
Start the ipdevpoll daemon
"""

# Assuming a production environment, we don't want to raise exceptions
# while logging
import logging
import platform

logging.raiseExceptions = False

from nav.bootstrap import bootstrap_django

bootstrap_django(__file__)

if __name__ == '__main__':
    if platform.system() == "Linux":
        from nav.ipdevpoll.epollreactor2 import install

        install()

    from nav.ipdevpoll.daemon import main

    main()
