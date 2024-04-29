#!/usr/bin/env python
# encoding: utf-8

"""
The NAV treshold monitor.
"""

# Assuming a production environment, we don't want to raise exceptions
# while logging
import logging

logging.raiseExceptions = False

from nav.bootstrap import bootstrap_django

bootstrap_django(__file__)

from nav.thresholdmon import main

if __name__ == '__main__':
    main()
