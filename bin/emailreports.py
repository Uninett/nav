#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- testargs: month -*-
# Copyright (C) 2016 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Sends email status reports"""

import argparse
import logging
import os

from nav.bootstrap import bootstrap_django

bootstrap_django(__file__)

from nav.web.business.reportengine import send_reports
from nav.models.profiles import ReportSubscription
from nav.logs import init_generic_logging

LOGFILE = 'emailreports.log'
_logger = logging.getLogger('emailreports')


def main(args):
    """Send all reports"""
    init_generic_logging(logfile=LOGFILE, stderr=False)
    send_reports(args.period)


def get_parser():
    """Define the parser"""
    parser = argparse.ArgumentParser()
    period_choices = [p[0] for p in ReportSubscription.PERIODS]
    parser.add_argument(
        'period', help='The period for this report', choices=period_choices
    )
    return parser


if __name__ == '__main__':
    main(get_parser().parse_args())
