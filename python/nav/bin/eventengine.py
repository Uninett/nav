#!/usr/bin/env python
# encoding: utf-8
# -*- testargs: -h -*-
"""
The NAV eventengine deamon
"""

# Assuming a production environment, we don't want to raise exceptions
# while logging
import logging

logging.raiseExceptions = False

from nav.bootstrap import bootstrap_django

bootstrap_django(__file__)

from nav.eventengine.daemon import main

if __name__ == '__main__':
    main()
