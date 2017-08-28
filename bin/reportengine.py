#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2016 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
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
from nav.web.business.reportengine import send_reports
from nav.models.profiles import ReportSubscription


def main(period):
    """Send all reports"""
    send_reports(period)


def get_parser():
    """Define the parser"""
    parser = argparse.ArgumentParser()
    choices = [p[0] for p in ReportSubscription.PERIODS]
    help_text = 'The period for this report'
    parser.add_argument('period', help=help_text, choices=choices)
    return parser


if __name__ == '__main__':
    args = get_parser().parse_args()
    main(args.period)
